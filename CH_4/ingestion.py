import chromadb
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
import os
from config import SCRIPT_DIR, POLICIES_PATH
from pathlib import Path



load_dotenv(dotenv_path=SCRIPT_DIR.parent / ".env")

EMBEDDING_MODEL= os.getenv("EMBEDDING_MODEL")

# 1. Load open-source embedding model
model = SentenceTransformer(EMBEDDING_MODEL)

# 2. Initialize persistent Chroma client (saves to a local folder)
client = chromadb.PersistentClient(path=str(SCRIPT_DIR / "policies_store"))

def get_existing_documents(collection_name: str) -> set[str]:
    """Returns a set of document_names already stored in the collection."""
    collection = client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"},
    )
    existing = collection.get(include=["metadatas"])
    return {
        meta["document_name"]
        for meta in existing["metadatas"]
        if meta and "document_name" in meta
    }


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """Splits text into overlapping character chunks."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end].strip())
        start += chunk_size - overlap
    return [c for c in chunks if c]


def store_chunks(collection_name: str, chunks: list[dict]) -> None:
    """
    Encodes and upserts document chunks into a ChromaDB collection.
    
    Each item in `chunks` should be a dict with keys:
    'id', 'text', and 'document_name'.
    """
    if not chunks:
        return

    collection = client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"}
    )

    texts = [c["text"] for c in chunks]
    chunk_embeddings = model.encode(texts, normalize_embeddings=True).tolist()

    collection.upsert(
        ids=[c["id"] for c in chunks],
        embeddings=chunk_embeddings,
        documents=texts,
        metadatas=[{"document_name": c["document_name"]} for c in chunks]
    )


def query_chunks(collection_name: str, question: str, top_k: int = 2) -> list[dict]:
    """
    Converts a user question to a vector and retrieves the top_k matching chunks.
    """
    collection = client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"}
    )

    query_vector = model.encode([question], normalize_embeddings=True).tolist()

    results = collection.query(
        query_embeddings=query_vector,
        n_results=top_k,
        include=["documents", "metadatas", "distances"]
    )

    matches = []
    for i in range(len(results["ids"][0])):
        matches.append({
            "rank": i + 1,
            "id": results["ids"][0][i],
            "document_name": results["metadatas"][0][i]["document_name"],
            "text": results["documents"][0][i],
            "similarity": round(1 - results["distances"][0][i], 4)
        })

    return matches


def ingest_documents(docs_dir: Path, collection_name: str = "policies") -> None:
    """Scans docs_dir for new files, chunks them, and stores them in ChromaDB."""
    if not docs_dir.exists():
        print(f"[Ingest] Folder not found: {docs_dir}")
        return

    existing_docs = get_existing_documents(collection_name)

    # Scan for .txt and .md files (extendable to .pdf if needed)
    files = [f for f in docs_dir.iterdir() if f.is_file() and f.suffix.lower() in {".txt", ".md"}]
    new_files = [f for f in files if f.name not in existing_docs]

    if not new_files:
        print("[Ingest] No new documents found.")
        return

    new_chunks = []
    for file_path in new_files:
        content = file_path.read_text(encoding="utf-8")
        parts = chunk_text(content)
        for idx, part in enumerate(parts, start=1):
            new_chunks.append({
                "id": f"{file_path.stem}_chunk_{idx:03d}",
                "text": part,
                "document_name": file_path.name,
            })

    store_chunks(collection_name=collection_name, chunks=new_chunks)
    print(f"[Ingest] Ingested {len(new_files)} new document(s) ({len(new_chunks)} chunks) into '{collection_name}'.")


# --- EXAMPLE USAGE ---
if __name__ == "__main__":
    demo_chunks = [
        {
            "id": "pol_001",
            "text": "Employees are entitled to 20 days of paid annual leave per calendar year.",
            "document_name": "leave_policy.pdf"
        },
        {
            "id": "pol_002",
            "text": "Remote work is permitted up to 3 days a week with manager approval.",
            "document_name": "remote_work_policy.pdf"
        },
        {
            "id": "pol_003",
            "text": "Travel expenses must be submitted with receipts within 14 days of return.",
            "document_name": "expense_policy.pdf"
        }
    ]

    # 1. Store chunks
    store_chunks(collection_name="policies", chunks=demo_chunks)

    # 2. Query chunks
    results = query_chunks(
        collection_name="policies",
        question="How many days can I work from home?",
        top_k=2
    )

    for r in results:
        print(f"Rank {r['rank']} | Similarity: {r['similarity']} | ID: {r['id']} | File: {r['document_name']}")
        print(f"Text: {r['text']}\n")