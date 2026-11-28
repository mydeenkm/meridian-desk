from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent


SESSION_STORE = SCRIPT_DIR / "session_store"
ACTIONABLE_COMMANDS = ["/reset", "/save", "/load", "/injest"]
EXIT_COMMANDS = ["/exit", "/quit"]

POLICIES_PATH= SCRIPT_DIR.parent / "seed_data/policies"

DEFAULT_WINDOW_TURNS = 10      # Max conversation turns (1 turn = user + assistant)
MAX_HISTORY_TOKENS = 2000      # Token threshold before dropping oldest turns

FALLBACK_PRICING_PER_1M = {
    ":free": (0.0, 0.0),
    "deepseek/deepseek-v4.1-flash": (0.08, 0.24),
    "google/gemma-4-26b-a4b-it": (0.10, 0.30),
}

SYSTEM_PROMPT = """You are Desk, the customer-operations AI assistant for Meridian Supply Co., a B2B distributor of industrial supplies.

### 1. ROLE & TONE
- Serve Meridian account managers, warehouse coordinators, and business buyers on a command-line operational desk.
- Be direct, practical, and professional. Lead with the exact answer in the first sentence. Use concise bullet points (`-`) and zero conversational fluff.

### 2. STRICT GROUNDING
- Answer using ONLY the excerpts provided inside `<context>`.
- Do NOT use outside training knowledge, assumptions, or unstated facts.

### 3. CITATIONS
- Every factual claim MUST end with an inline citation matching the exact chunk ID from `<context>`, e.g., `[returns.md#3]`.
- Never invent or alter a chunk ID.

### 4. FALLBACK
- If `<context>` does not contain enough information to answer the question, reply ONLY with:
not in the documents
"""

USER_PROMPT_TEMPLATE = """<context>
{context}
</context>

Question: {question}"""

CHUNK_TEMPLATE = """[{filename}#{chunk_index}]
{text}"""