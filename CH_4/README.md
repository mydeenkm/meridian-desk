# Challenge 4 — Naive RAG (Meridian Desk)

## Overview
Implemented a local Retrieval-Augmented Generation (RAG) pipeline for Meridian Supply Co.'s operational CLI (`desk`). The assistant ingests company policy documents into a persistent vector database and answers policy questions strictly from retrieved context with inline `[filename#chunk]` citations, falling back to `not in the documents` when the answer is not present.

## Architecture & Implementation
- **`config.py`**: Centralizes paths (`seed_data/policies`, `session_store`), sliding-window limits (`MAX_HISTORY_TOKENS = 2000`), and the three RAG prompt templates:
  - `SYSTEM_PROMPT`: Enforces Desk persona, strict `<context>`-only grounding, `[filename#chunk_index]` citations, and the exact `not in the documents` fallback.
  - `USER_PROMPT_TEMPLATE`: Wraps retrieved chunks in `<context>...</context>` above the user's question.
  - `CHUNK_TEMPLATE`: Stamps each retrieved chunk with `[{filename}#{chunk_index}]`.
- **`ingestion.py`**:
  - Splits `.md`/`.txt` policy files into fixed-size chunks (`chunk_size=500`, `overlap=50`).
  - Embeds chunks locally using `SentenceTransformer` (`EMBEDDING_MODEL`, cosine-normalized) and stores them in a persistent **ChromaDB** collection (`./policies_store`).
  - **Idempotent ingest**: Checks `get_existing_documents()` and uses deterministic chunk IDs (`{stem}_chunk_{idx:03d}`) with `collection.upsert()` so re-running `/injest` never creates duplicates.
- **`llm_client.py`**:
  - `build_user_prompt()` retrieves the top 4 chunks (`top_k=4`) from ChromaDB, formats them with `CHUNK_TEMPLATE`, and injects them into `USER_PROMPT_TEMPLATE`.
  - Streams responses via the OpenAI SDK with exponential-backoff retries (`max_attempts=3`) and tracks token usage, latency, and estimated cost.
- **`main.py` & `session.py`**:
  - Provides the interactive `desk` CLI with `/injest`, `/save`, `/load`, `/reset`, and `/exit` commands, plus a token-budget sliding window for multi-turn sessions.

## Evaluation Results (11 Test Queries)

| # | Type | Question | Desk Answer & Citation | Result |
|---|---|---|---|---|
| 1 | In-Scope | Invoice dispute window & payment during dispute? | 30 days from invoice date `[billing-disputes-policy.md#1]`; undisputed amount due by original due date `[billing-disputes-policy.md#2]`. | Pass |
| 2 | In-Scope | 15 units of SKU A + 15 units of SKU B — 6% bulk discount? | No; SKUs aren't combined, so each 15-unit line gets 3% `[bulk-pricing-policy.md#1]`; must be requested on order/quote `[bulk-pricing-policy.md#2]`. | Pass |
| 3 | In-Scope | 3-year-old account — Net 60 payment terms? | No; Tier C gets Net 45; Net 60+ not offered `[credit-terms-policy.md#1]`. | Pass |
| 4 | In-Scope | Late fee & credit hold threshold? | 1.5% monthly late fee; credit hold after >15 days past due `[credit-terms-policy.md#1]`. | Pass |
| 5 | In-Scope | Damaged shipment reporting window & return freight? | 5 business days from delivery; Meridian pays return freight for confirmed MS error/carrier damage `[damaged-or-incorrect-shipments-policy.md#1]`. | Pass |
| 6 | Multi-Doc | Combine 2% early-payment discount with 10% bulk discount? | No; cannot be combined `[credit-terms-policy.md#3]` `[bulk-pricing-policy.md#1]` `[bulk-pricing-policy.md#2]`. | Pass |
| 7 | Multi-Doc | In-stock hazmat processing time & extra fee? | Ships within 5 business days (2 + 3); $75 hazmat handling fee `[shipping-policy.md#3]` `[hazardous-goods-policy.md#2]`. | Pass |
| 8 | In-Scope | Backorder Policy (POL-BKO-01) for out-of-stock items? | Zero-stock items can be ordered and ship in 10–15 business days `[backorder-and-stock-policy.md#1]`. | Pass |
| 9 | Out-of-Scope | Difference between LTL and FTL freight in general logistics? | `not in the documents` | Pass |
| 10 | Out-of-Scope | Does Meridian accept Amex or crypto for invoice payments? | `not in the documents` | Pass |
| 11 | Out-of-Scope | What is the weather in Chicago today? | `not in the documents` | Pass |

### Summary
- **Overall Accuracy:** **11 / 11 (100%)**
- **In-Scope Policy Q&A:** **8 / 8** accurate with valid inline citations (including 2 multi-document synthesis questions).
- **Out-of-Scope Refusal:** **3 / 3** returned the exact `not in the documents` fallback (including general logistics and near-miss Meridian payment questions).
- **Session Metrics:** 22,746 total tokens across 11 turns | ~2.1s average latency per turn.

