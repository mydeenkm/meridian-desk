#!/usr/bin/env python3
import argparse
import os
import sys
from dotenv import load_dotenv
from openai import OpenAI

from config import SCRIPT_DIR, SYSTEM_PROMPT, EXIT_COMMANDS, ACTIONABLE_COMMANDS
from llm_client import ask_desk
from session import apply_sliding_window, handle_command, new_session_stats



load_dotenv(dotenv_path=SCRIPT_DIR.parent / ".env")



def process_turn(
    client: OpenAI,
    model: str,
    messages: list[dict],
    stats: dict,
    user_input: str,
    is_startup: bool = False,
    debug: bool = False
) -> tuple[list[dict], dict]:
    try:
        if user_input.startswith("/"):
            return handle_command(user_input, messages, stats, is_startup=is_startup)

        # Enforce sliding window (max 10 turns & token budget) before calling API
        messages, dropped = apply_sliding_window(messages)
        
        if dropped > 0:
            print(f"[Desk] Sliding window trimmed {dropped} oldest turn(s) to stay within limits.")


        result = ask_desk(client, model, messages, user_input, temperature=1, debug=debug)
        messages.append({"role": "assistant", "content": result["reply"]})

        # Per-turn metrics
        turn_in = result["input_tokens"]
        turn_out = result["output_tokens"]
        turn_total = turn_in + turn_out

        # Update running session totals
        stats["input_tokens"] += turn_in
        stats["output_tokens"] += turn_out
        stats["total_tokens"] += turn_total
        stats["cost"] += result["cost"]

        active_turns = (len(messages) - 1) // 2
        print(
            f"---\n"
            f"Turn Tokens   : {turn_in} in / {turn_out} out ({turn_total} total) | "
            f"Latency: {result['latency']:.2f}s | Cost: ${result['cost']:.6f}\n"
            f"Session Total : {stats['input_tokens']} in / {stats['output_tokens']} out "
            f"({stats['total_tokens']} total) | Active Window: {active_turns} turn(s) | "
            f"Total Cost: ${stats['cost']:.6f}\n"
        )
    except Exception as e:
        print(f"Error: {e}\n", file=sys.stderr)
    return messages, stats


def main():
    parser = argparse.ArgumentParser(description="Desk CLI Assistant")
    parser.add_argument("command", nargs="?", help="Optional subcommand (e.g., chat)")
    parser.add_argument("question", nargs="*", help="Optional initial question")
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Print retrieved chunks and similarity scores",
    )
    parsed_args = parser.parse_args()

    api_key = os.getenv("API_KEY")
    base_url = os.getenv("END_POINT")
    model = os.getenv("DEPLOYEMENT_NAME")
    print(f"[DEBUG MODE: {parsed_args.debug}]")
    if not api_key:
        print(
            "Error: Set OPENAI_API_KEY or OPENROUTER_API_KEY in your .env file or environment.",
            file=sys.stderr,
        )
        sys.exit(1)

    client = OpenAI(base_url=base_url, api_key=api_key)
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    stats = new_session_stats()
    print("Desk Assistant started. Type '/exit' or '/quit' to close.\n")
    print("ACTIONABLE_COMMANDS: {}\n".format(ACTIONABLE_COMMANDS))

    initial_question = (
        " ".join(parsed_args.question).strip()
        if parsed_args.command == "chat" and parsed_args.question
        else ""
    )
    if initial_question:
        print(f"You: {initial_question}")
        messages, stats = process_turn(
            client, model, messages, stats, initial_question, is_startup=True,debug=parsed_args.debug,
        )

    while True:
        try:
            question = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nClosing Desk. Goodbye!")
            break

        if not question:
            continue

        if question.lower() in EXIT_COMMANDS:
            print("Closing Desk. Goodbye!")
            break

        messages, stats = process_turn(
            client, model, messages, stats, question, is_startup=False, debug=parsed_args.debug
        )


if __name__ == "__main__":
    main()