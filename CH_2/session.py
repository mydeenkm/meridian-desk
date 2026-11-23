import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from config import (
    ACTIONABLE_COMMANDS,
    MAX_HISTORY_TOKENS,
    SESSION_STORE,
    SYSTEM_PROMPT,
)


def new_session_stats() -> dict:
    return {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0, "cost": 0.0}


def estimate_message_tokens(msg: dict) -> int:
    # ~4 chars per token heuristic + per-message role overhead
    return (len(msg.get("content", "")) // 4) + 4


def apply_sliding_window(
    messages: list[dict],
    max_tokens: int = MAX_HISTORY_TOKENS,
) -> tuple[list[dict], int]:
    # Nothing to trim if only system prompt (len 1) or system + first user message (len 2)
    if len(messages) <= 2:
        return messages, 0

    pinned = messages[:2]        # [system_msg, first_user_msg]
    history = messages[2:]       # Remaining conversation messages eligible for trimming
    dropped_turns = 0

    def current_tokens(msgs: list[dict]) -> int:
        return sum(estimate_message_tokens(m) for m in pinned) + sum(
            estimate_message_tokens(m) for m in msgs
        )

    # Drop oldest messages from `history` until within token limit (keep at least 1 trailing msg if needed)
    while len(history) > 1 and current_tokens(history) > max_tokens:
        drop_count = 2 if len(history) >= 3 else 1
        history = history[drop_count:]
        dropped_turns += 1

    return pinned + history, dropped_turns

def sanitize_filename(name: str | None) -> str | None:
    if not name:
        return None
    base_name = Path(name.strip()).name
    clean_name = re.sub(r"[^a-zA-Z0-9_-]", "", base_name)
    return clean_name or None


def parse_command_and_arg(text: str) -> tuple[str, str | None]:
    parts = text.split(maxsplit=1)
    command = parts[0].lower() if parts else ""
    raw_arg = parts[1] if len(parts) > 1 else None
    return command, sanitize_filename(raw_arg)


def save_session(messages: list[dict], file_name: str | None, stats: dict) -> None:
    if not file_name:
        print("[Error] Usage: /save <valid_filename>")
        return

    os.makedirs(SESSION_STORE, exist_ok=True)
    filepath = SESSION_STORE / f"{file_name}.json"
    chat_history = [m for m in messages if m["role"] != "system"]
    payload = {
        "saved_at": datetime.now(timezone.utc).isoformat(),
        "message_count": len(chat_history),
        "session_totals": stats,
        "messages": chat_history,
    }
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    print(f"[Desk] Saved {len(chat_history)} messages to {filepath}")


def load_session(
    messages: list[dict], file_name: str | None, stats: dict
) -> tuple[list[dict], dict]:
    if not file_name:
        print("[Error] Usage: /load <valid_filename>")
        return messages, stats

    filepath = SESSION_STORE / f"{file_name}.json"
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        loaded_msgs = data.get("messages", [])
        loaded_stats = data.get("session_totals", new_session_stats())
        restored, dropped = apply_sliding_window(
            [{"role": "system", "content": SYSTEM_PROMPT}] + loaded_msgs
        )
        print(f"[Desk] Loaded session '{file_name}' ({len(restored) - 1} messages).")
        if dropped > 0:
            print(f"[Desk] Trimmed {dropped} oldest turn(s) to fit active window limits.")
        return restored, loaded_stats
    except FileNotFoundError:
        print(f"[Error] Session '{file_name}' not found.")
    except (json.JSONDecodeError, KeyError):
        print(f"[Error] Session file '{filepath}' is corrupted. Current session kept.")
    return messages, stats


def handle_command(
    text: str, messages: list[dict], stats: dict, is_startup: bool = False
) -> tuple[list[dict], dict]:
    command, file_name = parse_command_and_arg(text)

    if command not in ACTIONABLE_COMMANDS:
        print(f"[Error] Pass a valid command in {ACTIONABLE_COMMANDS}")
        return messages, stats

    if command == "/reset":
        if is_startup:
            print("[Desk] Not applicable at startup.")
            return messages, stats
        print("[Desk] Session and token counters reset.")
        return [{"role": "system", "content": SYSTEM_PROMPT}], new_session_stats()

    if command == "/save":
        if is_startup:
            print("[Desk] Not applicable at startup.")
            return messages, stats
        save_session(messages, file_name, stats)
        return messages, stats

    if command == "/load":
        return load_session(messages, file_name, stats)

    return messages, stats