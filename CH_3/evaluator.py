import json
import os
import textwrap
from itertools import zip_longest
from pathlib import Path
from dotenv import load_dotenv
from pydantic import ValidationError
from config import (
    GROUND_TRUTH_PATH,
    RESULTS_M1_PATH,
    RESULTS_M2_PATH,
    SCRIPT_DIR,
)
from schema import OrderRequest

load_dotenv(dotenv_path=SCRIPT_DIR.parent / ".env")


def load_json(path: Path) -> dict[str, dict]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def validate_ground_truth(data: dict | None) -> tuple[bool, str]:
    if not isinstance(data, dict):
        return False, "MISSING OR INVALID JSON OBJECT"
    payload = {**data, "confidence": data.get("confidence", 1.0)}
    try:
        validated = OrderRequest.model_validate(payload)
        return True, validated.model_dump_json(indent=2, exclude={"confidence"})
    except ValidationError as exc:
        errors = "; ".join(f"{e['loc']}: {e['msg']}" for e in exc.errors())
        return False, f"SCHEMA ERROR -> {errors}"


def format_prediction(pred: dict | None) -> tuple[str, int]:
    if not isinstance(pred, dict):
        return "MISSING PREDICTION", 0

    attempts = int(pred.get("attempts", 1))
    display_dict = {k: v for k, v in pred.items() if k != "attempts"}
    return json.dumps(display_dict, indent=2), attempts


def wrap_block(text: str, width: int) -> list[str]:
    """Splits text into lines and wraps any line exceeding column width."""
    wrapped_lines: list[str] = []
    for raw_line in text.splitlines():
        if not raw_line:
            wrapped_lines.append("")
        else:
            wrapped_lines.extend(
                textwrap.wrap(
                    raw_line,
                    width=width,
                    replace_whitespace=False,
                    drop_whitespace=False,
                )
            )
    return wrapped_lines


def print_horizontal_comparison(
    headers: tuple[str, str, str],
    blocks: tuple[str, str, str],
    col_width: int = 44,
) -> None:
    """Renders 3 multi-line JSON blocks side-by-side in a horizontal table."""
    sep = "+" + "+".join("-" * (col_width + 2) for _ in range(3)) + "+"

    print(sep)
    print(
        f"| {headers[0][:col_width]:<{col_width}} "
        f"| {headers[1][:col_width]:<{col_width}} "
        f"| {headers[2][:col_width]:<{col_width}} |"
    )
    print(sep)

    c1_lines = wrap_block(blocks[0], col_width)
    c2_lines = wrap_block(blocks[1], col_width)
    c3_lines = wrap_block(blocks[2], col_width)

    for l1, l2, l3 in zip_longest(c1_lines, c2_lines, c3_lines, fillvalue=""):
        print(
            f"| {l1:<{col_width}} "
            f"| {l2:<{col_width}} "
            f"| {l3:<{col_width}} |"
        )

    print(sep)


def prompt_scores(m1_name: str, m2_name: str) -> tuple[float, float]:
    while True:
        raw = input(
            f"\nEnter score for [{m1_name}, {m2_name}] between 0 and 1 (e.g., '0.8, 0.5'): "
        ).strip()
        parts = [p.strip() for p in raw.split(",")]
        if len(parts) == 2:
            try:
                s1, s2 = float(parts[0]), float(parts[1])
                if 0.0 <= s1 <= 1.0 and 0.0 <= s2 <= 1.0:
                    return s1, s2
            except ValueError:
                pass
        print("Invalid input. Enter two numbers between 0 and 1 separated by a comma (e.g., 1, 0.75).")


def main() -> None:
    model_1 = os.getenv("DESK_MODEL_1", "Model 1")
    model_2 = os.getenv("DESK_MODEL_2", "Model 2")

    raw_gt = load_json(GROUND_TRUTH_PATH)
    m1_preds = load_json(RESULTS_M1_PATH)
    m2_preds = load_json(RESULTS_M2_PATH)

    total = len(raw_gt)
    m1_score = 0.0
    m2_score = 0.0
    m1_total_attempts = 0
    m2_total_attempts = 0

    for idx, (mail_id, gt_dict) in enumerate(raw_gt.items(), start=1):
        gt_ok, gt_display = validate_ground_truth(gt_dict)
        if not gt_ok:
            raise ValueError(f"Ground truth invalid for '{mail_id}': {gt_display}")

        m1_display, m1_attempts = format_prediction(m1_preds.get(mail_id).get("data"))
        m2_display, m2_attempts = format_prediction(m2_preds.get(mail_id).get("data"))

        m1_total_attempts += m1_attempts
        m2_total_attempts += m2_attempts

        print(f"\n[{idx}/{total}] EMAIL: {mail_id}")
        print_horizontal_comparison(
            headers=(
                "GROUND TRUTH",
                f"{model_1} (attempts: {m1_attempts})",
                f"{model_2} (attempts: {m2_attempts})",
            ),
            blocks=(gt_display, m1_display, m2_display),
            col_width=44,
        )

        s1, s2 = prompt_scores(model_1, model_2)
        m1_score += s1
        m2_score += s2

    m1_acc = (m1_score / total) * 100 if total else 0.0
    m2_acc = (m2_score / total) * 100 if total else 0.0
    m1_avg_att = (m1_total_attempts / total) if total else 0.0
    m2_avg_att = (m2_total_attempts / total) if total else 0.0

    m1_score_str = f"{m1_score:.2f}/{total}"
    m2_score_str = f"{m2_score:.2f}/{total}"

    print("\n" + "=" * 72)
    print(f"FINAL EVALUATION SUMMARY ({total} emails)")
    print("=" * 72)
    header = f"{'Metric':<24} | {model_1:<20} | {model_2:<20}"
    print(header)
    print("-" * len(header))
    print(f"{'Total Score':<24} | {m1_score_str:>20} | {m2_score_str:>20}")
    print(f"{'Accuracy %':<24} | {m1_acc:>19.2f}% | {m2_acc:>19.2f}%")
    print(f"{'Total Attempts':<24} | {m1_total_attempts:>20} | {m2_total_attempts:>20}")
    print(f"{'Avg Attempts / Email':<24} | {m1_avg_att:>20.2f} | {m2_avg_att:>20.2f}")
    print("=" * 72)


if __name__ == "__main__":
    main()