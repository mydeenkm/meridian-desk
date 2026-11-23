#!/usr/bin/env python3
import argparse
import os
import random
import sys
import time
from pathlib import Path
from dotenv import load_dotenv
from openai import APIConnectionError, APITimeoutError, OpenAI, RateLimitError

# Always load .env from the project root directory (even when run from CH_2/ or via symlink)
SCRIPT_DIR = Path(__file__).resolve().parent
load_dotenv(dotenv_path=SCRIPT_DIR.parent / ".env")

SYSTEM_PROMPT = """You are Desk, the customer-operations assistant for Meridian Supply Co., a B2B distributor of industrial supplies (safety gear, MRO hardware, fasteners, electrical components, and packaging materials).

Your Role & Tone:
- Assist Meridian account managers, warehouse coordinators, and business buyers with operational questions.
- Communicate in a concise, practical, and professional B2B tone suited for a command-line interface—lead with the direct answer and use short bullet points when listing steps or options.

Boundaries (Current Capabilities):
- You do NOT yet have live access to Meridian's order database, inventory system, ERP, or internal policy documents.
- Never invent or guess order statuses, tracking numbers, SKU stock levels, account pricing, or specific return/refund policy terms.
- If a user asks about a specific order, live inventory, or refund processing, state clearly that live system lookups are not connected yet and explain what information (e.g., PO number, order ID, SKU) will be needed once available.
- For general industrial supply, procurement, or B2B logistics questions, provide helpful, accurate guidance.
"""

FALLBACK_PRICING_PER_1M = {
    ":free": (0.0, 0.0),
    "deepseek/deepseek-v4.1-flash": (0.08, 0.24),
    "google/gemma-4-26b-a4b-it": (0.10, 0.30),
}


def estimate_cost(usage, model: str) -> float:
    if usage is None:
        return 0.0
    raw_cost = getattr(usage, "cost", None)
    if raw_cost is not None:
        return float(raw_cost)
    if model.endswith(":free"):
        return 0.0

    in_rate, out_rate = FALLBACK_PRICING_PER_1M.get(model, (0.0, 0.0))
    prompt_tokens = getattr(usage, "prompt_tokens", 0) or 0
    completion_tokens = getattr(usage, "completion_tokens", 0) or 0
    return (prompt_tokens / 1_000_000) * in_rate + (completion_tokens / 1_000_000) * out_rate


def ask_desk(
    client: OpenAI,
    model: str,
    messages: list[dict],
    question: str,
    temperature: float | None = None,
) -> dict:
    messages.append({"role": "user", "content": question})

    max_attempts = 3
    base_delay = 1.0

    for attempt in range(1, max_attempts + 1):
        start_time = time.perf_counter()
        try:
            res = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                timeout=30.0,
            )
            latency_sec = time.perf_counter() - start_time

            reply = res.choices[0].message.content or ""
            messages.append({"role": "assistant", "content": reply})

            usage = res.usage
            input_tokens = getattr(usage, "prompt_tokens", 0) or 0
            output_tokens = getattr(usage, "completion_tokens", 0) or 0
            cost = estimate_cost(usage, model)

            return {
                "reply": reply,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "latency": latency_sec,
                "cost": cost,
            }

        except (RateLimitError, APITimeoutError, APIConnectionError) as exc:
            if attempt == max_attempts:
                raise RuntimeError(
                    f"Request failed after {max_attempts} attempts: {exc}"
                ) from exc

            sleep_time = base_delay * (2 ** (attempt - 1)) + random.uniform(0, 0.25)
            print(
                f"[Retry {attempt}/{max_attempts - 1}] {type(exc).__name__} — waiting {sleep_time:.2f}s...",
                file=sys.stderr,
            )
            time.sleep(sleep_time)


def main():
    parser = argparse.ArgumentParser(description="Desk CLI Assistant")
    parser.add_argument("command", help="Subcommand (e.g., ask)")
    parser.add_argument("question", nargs="+", help="Question to ask Desk")
    parser.add_argument(
        "--model",
        default=os.getenv("DESK_MODEL") or "openrouter/free",
        help="Override model ID from DESK_MODEL",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=None,
        help="Sampling temperature (e.g., 0.0 to 1.0)",
    )
    parser.add_argument(
        "--compare",
        action="store_true",
        help="Run the question 5 times each at temperature 0 and 1",
    )
    parsed_args = parser.parse_args()

    if parsed_args.command != "ask":
        print('Usage: desk ask "your question"', file=sys.stderr)
        sys.exit(1)

    question = " ".join(parsed_args.question).strip()
    if not question:
        print("Error: Question cannot be empty.", file=sys.stderr)
        sys.exit(1)

    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("OPENROUTER_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL") or "https://openrouter.ai/api/v1"
    model = parsed_args.model
    temperature = parsed_args.temperature

    if not api_key:
        print(
            "Error: Set OPENAI_API_KEY or OPENROUTER_API_KEY in your .env file or environment.",
            file=sys.stderr,
        )
        sys.exit(1)

    client = OpenAI(base_url=base_url, api_key=api_key)

    # Stretch mode: run 5x at temperature 0.0 and 5x at temperature 1.0
    if parsed_args.compare:
        print(f"Comparing model: {model}\nQuestion: {question}")
        for temp in (0.0, 1.0):
            print(f"\n==================== TEMPERATURE {temp} ====================")
            for run in range(1, 6):
                fresh_messages = [{"role": "system", "content": SYSTEM_PROMPT}]
                try:
                    res = ask_desk(
                        client, model, fresh_messages, question, temperature=temp
                    )
                    print(f"[Run {run}] {res['reply']}")
                    print(
                        f"  -> Tokens: {res['input_tokens']} in / {res['output_tokens']} out | "
                        f"Latency: {res['latency']:.2f}s | Est. Cost: ${res['cost']:.6f}\n"
                    )
                except Exception as e:
                    print(f"[Run {run}] Error: {e}\n", file=sys.stderr)
        return

    # One-shot request mode
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    try:
        result = ask_desk(client, model, messages, question, temperature=temperature)
        print(result["reply"])
        print(
            f"\n---\n"
            f"Tokens: {result['input_tokens']} in / {result['output_tokens']} out | "
            f"Latency: {result['latency']:.2f}s | "
            f"Est. Cost: ${result['cost']:.6f}"
        )
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()