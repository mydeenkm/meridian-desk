from intelligence import parser_agent
from dotenv import load_dotenv
import os
from openai import OpenAI
from config import (
    SCRIPT_DIR,
    SEED_EMAILS_DIR,
    NEEDS_REVIEW_M1_PATH,
    RESULTS_M1_PATH,
    NEEDS_REVIEW_M2_PATH,
    RESULTS_M2_PATH,
)
from pathlib import Path
import json

load_dotenv(dotenv_path=SCRIPT_DIR.parent / ".env")


def load_text_files(directory_path: str) -> dict[str, str]:
    folder = Path(directory_path)
    files_data = {}

    for file_path in sorted(folder.glob("*.txt")):
        file_name = str(file_path.name).split(".")[0]
        files_data[file_name] = file_path.read_text(encoding="utf-8")
    return files_data


def run_extraction_for_model(
    client: OpenAI,
    model: str,
    emails: dict[str, str],
    results_path: Path,
    needs_review_path: Path,
) -> dict[str, dict]:
    print(f"\n--- Running extraction with model: {model} ---")
    results = {}
    need_review_result = {}

    for mail, content in emails.items():
        print(f"[{model}] Processing mail {mail}...")
        response = parser_agent(
            client=client, model=model, mail=content, temperature=0.1
        )
        if isinstance(response, dict):
            results[mail] = response
            if response.get("status") == "need_review":
                need_review_result[mail] = response

    if need_review_result:
        with needs_review_path.open("w", encoding="utf-8") as f:
            json.dump(need_review_result, f, indent=2)

    if results:
        with results_path.open("w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)

    return results


def main():
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL")
    model_1 = os.getenv("DESK_MODEL_1")
    model_2 = os.getenv("DESK_MODEL_2")

    client = OpenAI(base_url=base_url, api_key=api_key)
    emails = load_text_files(f"{SEED_EMAILS_DIR}/emails")
    
    run_extraction_for_model(
        client=client,
        model=model_1,
        emails=emails,
        results_path=RESULTS_M1_PATH,
        needs_review_path=NEEDS_REVIEW_M1_PATH,
    )

    run_extraction_for_model(
        client=client,
        model=model_2,
        emails=emails,
        results_path=RESULTS_M2_PATH,
        needs_review_path=NEEDS_REVIEW_M2_PATH,
    )


if __name__ == "__main__":
    main()