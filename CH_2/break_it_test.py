#!/usr/bin/env python3
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent


def run_desk_cli(turns: list[str]) -> str:
    """Runs `desk chat`, streams stdout live to terminal, and returns full output."""
    cli_input = "\n".join(turns + ["exit"]) + "\n"
    proc = subprocess.Popen(
        ["desk", "chat"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    proc.stdin.write(cli_input)
    proc.stdin.close()

    output_lines = []
    for line in proc.stdout:
        print(line, end="", flush=True)
        output_lines.append(line)

    proc.wait()
    return "".join(output_lines)


# ==============================================================================
# BREAK IT — TEST 1: 5 Customer Emails via `desk` CLI (3 Runs)
# ==============================================================================
CUSTOMER_EMAILS = (
    "Extract the order lines from these 5 customer emails: "
    "1) rachel@apexmfg.com PO 9912: 50 boxes SKU-104 Nitrile Gloves, 10 cases SKU-882 Stretch Wrap. "
    "2) dave@northstarbuild.io PO NS-440: 200 units SKU-316B hex bolts. "
    "3) priya@metrologistics.in No PO: 25 rolls SKU-901 bubble wrap, 100 SKU-905 cartons. "
    "4) tom@weldpro.net PO 7731: 15 SKU-220 welding helmets, 30 pairs SKU-109 cut gloves. "
    "5) lin@clearwaterhvac.com PO CW-88: 12 rolls SKU-510 electrical tape, 5 boxes SKU-514 wire nuts."
)


def test_email_extraction_via_cli() -> list[dict]:
    print("\n=== TEST 1: 5 Customer Emails via `desk` CLI (3 Runs) ===")
    runs_data = []

    for run in range(1, 4):
        print(f"\n--- Run {run}/3 ---")
        full_output = run_desk_cli([CUSTOMER_EMAILS])
        try:
            parsed = json.loads(full_output)
            json_valid = True
            error_msg = None
            print(f"[Run {run}] json.loads() SUCCEEDED! Type: {type(parsed).__name__}")
        except json.JSONDecodeError as e:
            json_valid = False
            error_msg = str(e)
            print(f"[Run {run}] json.loads() FAILED (expected): {e}")

        runs_data.append(
            {
                "run": run,
                "json_valid": json_valid,
                "json_error": error_msg,
                "full_cli_output": full_output,
            }
        )

    return runs_data


# ==============================================================================
# BREAK IT — TEST 2: 40-Turn Chat via `desk` CLI -> Recall Turn 2 Fact
# ==============================================================================
def test_40_turns_via_cli() -> dict:
    print("\n=== TEST 2: 40-Turn Chat via `desk` CLI -> Recall Turn 2 Fact ===")
    turn_2_fact = "Remember this industrial PPE standard code: ANSI Z87.1-2020 for safety eyewear."
    turns = [
        "What does Meridian Supply Co. distribute?",  # Turn 1 (Pinned)
        turn_2_fact,                                    # Turn 2 (Evicted by sliding window)
    ]

    for t in range(3, 41):
        turns.append(f"Turn {t}: What is the difference between LTL and FTL freight?")

    recall_q = "What specific ANSI standard code did I mention in Turn 2?"
    turns.append(recall_q)

    full_output = run_desk_cli(turns)

    return {
        "method": "subprocess `desk chat` CLI",
        "total_turns": 40,
        "turn_2_fact": turn_2_fact,
        "recall_question": recall_q,
        "full_cli_output": full_output,
    }


if __name__ == "__main__":
    test_1_results = test_email_extraction_via_cli()
    test_2_results = test_40_turns_via_cli()

    full_report = {
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "experiment_1_email_drift": test_1_results,
        "experiment_2_challenge9_memory_eviction": test_2_results,
    }

    report_path = SCRIPT_DIR / "break_it_full_results.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(full_report, f, indent=2)

    print(f"\n[Saved full un-truncated JSON report to {report_path}]")