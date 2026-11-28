# Challenge 3 — Structured Extraction & Model Evaluation

## Overview
Built a structured order-extraction pipeline for Meridian Supply Co. that converts raw B2B customer emails into validated `OrderRequest` JSON records, automatically repairs validation errors, and compares two models side-by-side against 15 hand-labeled ground-truth emails.

## How It Works
1. **Schema (`schema.py`)**: Defined strict Pydantic models (`OrderRequest`, `LineItem`, `IntentType`, `UrgencyType`) with `extra="forbid"` and a strict JSON Schema generator.
2. **Configuration (`config.py`)**: Centralized file paths, `MAX_REPAIR_ATTEMPTS = 2`, and the extraction system prompt with Meridian edge-case rules (company vs. sender fallback, partial returns, relative dates, and urgency levels).
3. **Extraction & Self-Healing (`extractor.py`)**: Calls the LLM with structured JSON output, validates responses with Pydantic, and retries up to 2 times with the exact validation error on failure before routing unresolved emails to `needs_review`.
4. **Batch Processing**: Ran all 30 seed emails (`email_01.txt`–`email_30.txt`) through both `qwen/qwen3.8-27b` and `openai/gpt-oss-20b`.
5. **Side-by-Side Evaluation (`evaluator.py`)**: Displayed **Ground Truth**, **Model 1**, and **Model 2** in a horizontal 3-column table across 15 hand-labeled emails (`ground_truth.json`) with 0–1 scoring.

## Evaluation Results (15 Hand-Labeled Emails)

```text
========================================================================
FINAL EVALUATION SUMMARY (15 emails)
========================================================================
Metric                   | qwen/qwen3.8-27b     | openai/gpt-oss-20b  
----------------------------------------------------------------------
Total Score              |             11.70/15 |             13.30/15
Accuracy %               |               78.00% |               88.67%
Total Attempts           |                   15 |                   12
Avg Attempts / Email     |                 1.00 |                 0.80
========================================================================