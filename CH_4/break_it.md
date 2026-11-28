# Challenge 4 — "Break It" Stress Test & Retrieval Audit

## Overview
Tested the Naive RAG pipeline (`desk ask --debug`) against 4 adversarial scenarios designed to expose common RAG failure modes: exact-code lookup, Markdown table slicing, conflicting document versions, and vague multi-turn follow-ups.

---

## Scenario Results

### 1. Exact SKU Search (`MS-VLV-0200`)
- **Query:** `What are the specs or policy for SKU MS-VLV-0200?`
- **Top Retrieved Chunks:**
  1. `damaged-or-incorrect-shipments-policy.md#1` (`0.6657`)
  2. `warranty-policy.md#2` (`0.6646`)
  3. `warranty-policy.md#3` (`0.6533`)
  4. `bulk-pricing-policy.md#4` (`0.6466`)
- **Desk Answer:** `not in the documents`
- **Verdict:** **Pass (Refusal) / Fragile (Retrieval)** — `MS-VLV-0200` is not in the policy docs, so the LLM correctly refused. However, dense search still returned 4 unrelated chunks with deceptively high similarity scores (`0.65–0.67`) triggered by the words `"SKU"` and `"policy"`. Without a similarity threshold or hybrid BM25/keyword search, exact SKU lookups will struggle once catalog data is added.

---

### 2. Answer Inside a Markdown Table
- **Query:** `Which carriers accept hazmat shipments?`
- **Top Retrieved Chunks:**
  1. `hazardous-goods-policy.md#1` (`0.7714`) — *broken 25-char fragment: `"th every hazmat shipment."`*
  2. `hazardous-goods-policy.md#2` (`0.7600`) — *contains the carrier table*
  3. `hazardous-goods-policy.md#3` (`0.7096`)
  4. `shipping-policy.md#4` (`0.6519`)
- **Desk Answer:** `Only XPO Logistics and Old Dominion accept hazmat shipments. [hazardous-goods-policy.md#2]`
- **Verdict:** **Pass (Rank 2)** — The answer was accurate, but fixed-character chunking (`500 chars`) sliced the document mid-word and pushed a useless trailing fragment (`"th every hazmat shipment."`) to **Rank 1** above the actual table.

---

### 3. Conflicting Policy Documents (`v1.3` vs `v2.0`)
- **Query:** `What is the return window and restocking fee for standard catalog items?`
- **Top Retrieved Chunks:**
  1. `returns-policy-v2.md#1` (`0.8287`) — *v2.0, Effective 2026-10-01 (21 days, 20%)*
  2. `returns-policy.md#2` (`0.8263`) — *v1.3, Effective 2026-03-01 (30 days, 15%)*
  3. `warranty-policy.md#3` (`0.7638`)
  4. `bulk-pricing-policy.md#4` (`0.7354`)
- **Desk Answer:** `Eligible standard catalog items may be returned within 21 days of delivery, and approved returns carry a 20% restocking fee. [returns-policy-v2.md#1]`
- **Verdict:** **Pass (Rank 1 — Narrow Margin)** — Desk picked the newer v2.0 policy, but both conflicting versions were injected into `<context>` with a similarity gap of only **`0.0024`**. There is no metadata filtering or version/effective-date enforcement to guarantee the latest policy always wins.

---

### 4. Vague Multi-Turn Follow-Up
- **Turn 1:** `What is the early payment discount?`
  - **Top Hit:** `credit-terms-policy.md#2` (**Rank 2**, `0.6775`) — Desk answered `2% within 10 days`.
- **Turn 2:** `what about for bulk?`
  - **Top Retrieved Chunks:**
    1. `bulk-pricing-policy.md#1` (`0.6712`)
    2. `bulk-pricing-policy.md#2` (`0.6449`)
    3. `returns-policy.md#3` (`0.5790`)
    4. `returns-policy-v2.md#4` (`0.5790`)
  - **Desk Answer:** Accurate full breakdown of bulk discount tiers (`3%–10%`, `250+` custom quote) and non-combinability rule.
- **Verdict:** **Pass (Rank 1 — Lucky Keyword)** — Succeeded only because `"bulk"` directly matched `bulk-pricing-policy.md`. Because `build_user_prompt()` embeds the raw follow-up string without conversation-aware query rewriting, a pronoun-only follow-up (e.g., *"what about for 50 units?"*) would fail retrieval.

---

## Honest Retrieval Accuracy (Baseline Numbers)

| Metric | Score | Breakdown |
|---|---|---|
| **Hit Rate@4 (In-Scope)** | **100.0% (4 / 4)** | Relevant chunk appeared in top 4 on all 4 in-scope queries |
| **MRR (Mean Reciprocal Rank)** | **0.75** | Ranks: `2` (0.50), `1` (1.00), `2` (0.50), `1` (1.00) |
| **Out-of-Scope Refusal** | **100.0% (1 / 1)** | Correctly returned `not in the documents` for `MS-VLV-0200` |
| **End-to-End Answer Accuracy** | **100.0% (5 / 5)** | All 5 answers were factually correct with valid citations |
