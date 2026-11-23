Here is your cleanly formatted, properly indented `README.md` ready to copy-paste into your repository:
# Meridian Desk CLI (`desk.py`)

A command-line customer-operations assistant for **Meridian Supply Co.**, built with the OpenAI Python SDK and OpenRouter.

---

## Architecture Breakdown

### 1. Setup & Guardrails
* **`load_dotenv()`**: Reads your `.env` file so your API key and default model load automatically without manual terminal exports.
* **`SYSTEM_PROMPT`**: Establishes the assistant's persona ("Desk" for Meridian Supply Co.) and enforces strict boundaries so it refuses to fabricate order statuses, stock levels, or policy terms prior to RAG/ERP integration.

### 2. Cost Calculator (`estimate_cost`)
* Reads OpenRouter's native `usage.cost` field (in USD credits) directly from the API response.
* Returns `$0.000000` for `:free` endpoints, or calculates estimated cost from input/output token counts using `FALLBACK_PRICING_PER_1M`.

### 3. Resilient API Caller (`ask_desk`)
* **Conversation Memory**: Appends user prompts and assistant replies to the in-memory `messages` list across turns within a single session.
* **Retry & Exponential Backoff**: Retries up to **3 times** on `RateLimitError`, `APITimeoutError`, and `APIConnectionError` with jittered backoff (`~1s` → `~2s`).
* **Telemetry**: Measures request latency using `time.perf_counter()` and returns token counts, latency, and estimated cost.

### 4. CLI Flags & Modes (`main`)
* **`argparse` Flags**: Supports `ask "<question>"`, `--model`, `--temperature`, and `--compare`.
* **Compare Mode (`--compare`)**: Runs an initial prompt 5 times at `temperature=0.0` and 5 times at `temperature=1.0`, resetting `messages` on every run for isolated comparison.
* **Interactive Loop (`while True`)**: Keeps the CLI session open for multi-turn dialogue until `exit`, `quit`, or `Ctrl+C`. Pops failed user messages on error to preserve valid chat history.

---

## Inputs & Outputs

### 1. General Domain Question

(desk-env) mydeen0302@DESKTOP-O7NOI15:~/azure-ml/meridian-desk$ python desk.py ask "When should a warehouse crew use ANSI Type I versus Type II safety helmets?"
Desk Assistant started (model: nvidia/nemotron-3-ultra-550b-a55b:free, temp: None). Type 'exit' or 'quit' to close.

You: When should a warehouse crew use ANSI Type I versus Type II safety helmets?

Desk: **ANSI Type I** — Top-impact protection only.  
**ANSI Type II** — Top **and** lateral (side, front, rear) impact protection.

### When to specify each

| Situation | Recommended Type |
|-----------|------------------|
| Overhead hazards only (falling tools, debris, materials) | **Type I** |
| Exposure to side/front/rear impacts (low beams, moving equipment, confined spaces, swing loads) | **Type II** |
| General construction, warehousing, logistics with mixed traffic | **Type II** (most versatile) |
| Dedicated overhead-only zones (e.g., rack aisles with no cross-traffic) | **Type I** acceptable |
| Any environment where workers bend, kneel, or work near mobile plant | **Type II** |

### Quick decision checklist
- **Lateral strike risk?** → Type II  
- **Only vertical falling objects?** → Type I (lighter, often lower cost)  
- **Uncertain or mixed tasks?** → Default to Type II

### Note on markings
Look for the ANSI/ISEA Z89.1-2014 (or later) label inside the shell:
- **Type I** = “Type I” only  
- **Type II** = “Type II” (will also list “Class G/E/C” for electrical rating)

If you need help matching specific Meridian SKUs to these types once inventory lookup is live, just share the part numbers or descriptions.
---
Tokens: 268 in / 361 out | Latency: 5.34s | Est. Cost: $0.000000


### 2. Temperature Comparison (`--compare`: `0.0` vs `1.0`)

(desk-env) mydeen0302@DESKTOP-O7NOI15:~/azure-ml/meridian-desk$ python desk.py ask "Draft a 2-sentence apology for a delayed fastener shipment" --compare
Comparing model: nvidia/nemotron-3-ultra-550b-a55b:free
Question: Draft a 2-sentence apology for a delayed fastener shipment

==================== TEMPERATURE 0.0 ====================
[Run 1] We apologize for the delay in your fastener shipment and understand the impact this has on your production schedule. A revised delivery date will be confirmed by end of business today.
  -> Tokens: 265 in / 82 out | Latency: 2.55s | Est. Cost: $0.000000

[Run 2] We apologize for the delay in your fastener shipment and understand the impact this has on your production schedule. A revised delivery date will be confirmed by end of business today.
  -> Tokens: 265 in / 82 out | Latency: 1.77s | Est. Cost: $0.000000

[Run 3] We apologize for the delay in your fastener shipment and understand the impact this has on your production schedule. A revised delivery date will be confirmed by end of business today.
  -> Tokens: 265 in / 82 out | Latency: 1.76s | Est. Cost: $0.000000

[Run 4] We apologize for the delay in your fastener shipment and understand the impact this has on your production schedule. A revised delivery date will be confirmed by end of business today.
  -> Tokens: 265 in / 82 out | Latency: 1.50s | Est. Cost: $0.000000

[Run 5] We apologize for the delay in your fastener shipment and understand the impact on your production schedule. A revised delivery date will be confirmed by end of business today.
  -> Tokens: 265 in / 69 out | Latency: 3.02s | Est. Cost: $0.000000


==================== TEMPERATURE 1.0 ====================
[Run 1] We apologize for the delay in your fastener shipment and understand the impact on your production schedule. Our logistics team is expediting the order and will confirm the revised delivery date by end of business today.
  -> Tokens: 265 in / 72 out | Latency: 1.77s | Est. Cost: $0.000000

[Run 2] We apologize for the delay in delivering your fastener order and understand the impact on your production schedule. Our logistics team is expediting the shipment and will provide an updated delivery date within the next business day.
  -> Tokens: 265 in / 68 out | Latency: 1.47s | Est. Cost: $0.000000

[Run 3] We apologize for the delay in your fastener shipment and understand the impact on your operations. We're actively expediting the order and will provide an updated delivery date by end of day.
  -> Tokens: 265 in / 65 out | Latency: 1.83s | Est. Cost: $0.000000

[Run 4] We apologize for the delay in delivering your fastener order and appreciate your patience while we expedite the shipment. A revised delivery date will be confirmed within the next business day.
  -> Tokens: 265 in / 62 out | Latency: 1.10s | Est. Cost: $0.000000

[Run 5] We apologize for the delay in your fastener shipment and understand the impact on your production schedule. Our logistics team is expediting the order and will confirm the revised delivery date by end of day.
  -> Tokens: 265 in / 66 out | Latency: 1.82s | Est. Cost: $0.000000


---

## "Break It" Stress Tests & Findings

### 1. Cross-Process Statelessness (`"My name is Ravi"` → `"What is my name?"`)


(desk-env) mydeen0302@DESKTOP-O7NOI15:~/azure-ml/meridian-desk$ python desk.py 
Desk Assistant started (model: nvidia/nemotron-3-ultra-550b-a55b:free, temp: None). Type 'exit' or 'quit' to close.

You: My Name is Ravi

Desk: Hello Ravi. How can I help you with Meridian Supply Co. operations today?
---
Tokens: 257 in / 48 out | Latency: 1.29s | Est. Cost: $0.000000

You: exit 
Closing Desk. Goodbye!

(desk-env) mydeen0302@DESKTOP-O7NOI15:~/azure-ml/meridian-desk$ python desk.py 
Desk Assistant started (model: nvidia/nemotron-3-ultra-550b-a55b:free, temp: None). Type 'exit' or 'quit' to close.

You: what is my name ?

Desk: I don't have access to your account information or identity. My current capabilities don't include live system lookups for user profiles or account details.

If you have a specific operational question—order status, inventory check, return process, shipping, etc.—let me know the relevant reference (PO number, order ID, SKU, account number) and I can guide you on the next steps or what information will be needed once live lookups are available.
---
Tokens: 257 in / 138 out | Latency: 1.94s | Est. Cost: $0.000000

You: exit 
Closing Desk. Goodbye!


### 2. Non-Streaming Latency on Complex Prompts (`51.07s` Blank Terminal)

(desk-env) mydeen0302@DESKTOP-O7NOI15:~/azure-ml/meridian-desk$ python desk.py 
Desk Assistant started (model: nvidia/nemotron-3-ultra-550b-a55b:free, temp: None). Type 'exit' or 'quit' to close.

You: "A key manufacturing client just reported that a mixed pallet of Grade 8 hex bolts, NEMA 4X electrical enclosures, and ANSI Type II safety helmets arrived with water damage on two cartons and three missing line items on the packing slip, while their assembly line shutdown starts in 36 hours. Walk me through a complete, step-by-step operational triage plan covering immediate containment, carrier claim documentation, replacement fulfillment options, and internal escalation—and clearly flag every step where you currently lack live ERP, inventory, or policy access along with the exact data fields our team will need to pull."

Desk: **MERIDIAN SUPPLY CO. – CRITICAL SHIPMENT TRIAGE PLAN**  
*Client: Key Manufacturing Account | Assembly-line shutdown in 36 hrs*  
*Issue: Water damage (2 cartons) + 3 missing line items on packing slip*  

---

### **PHASE 1 – IMMEDIATE CONTAINMENT (0–2 hrs)**
| Step | Action | Live System Access Needed? | Exact Data Fields Required |
|------|--------|----------------------------|----------------------------|
| 1.1 | Acknowledge client via phone/email; confirm shutdown deadline & exact impact | ❌ No | Client PO#, Meridian Order ID, Contact name/phone/email |
| 1.2 | Quarantine affected pallet in client’s receiving area; photograph damage & packing slip | ❌ No | Photos (damage, labels, packing slip), Pallet ID, Carton IDs |
| 1.3 | Verify packing slip vs. client PO vs. Meridian shipment manifest | ⚠️ **Yes – ERP/WMS** | PO line items, Meridian SO#, Shipment manifest (SKU, Qty, Lot#, Serial#) |
| 1.4 | Identify 3 missing SKUs & 2 water-damaged SKUs; segregate salvageable stock | ⚠️ **Yes – WMS** | SKU, Qty ordered, Qty received, Qty damaged, Lot/Serial#, Bin location |
| 1.5 | Notify carrier (driver/supervisor) on-site; request exception notation on POD | ❌ No | Carrier name, PRO/BOL#, Driver name, POD exception verbiage |

---

### **PHASE 2 – CARRIER CLAIM DOCUMENTATION (2–6 hrs)**
| Step | Action | Live System Access Needed? | Exact Data Fields Required |
|------|--------|----------------------------|----------------------------|
| 2.1 | File carrier claim within 24-hr window (photos, POD exception, commercial invoice) | ❌ No | Claim form, Photos, POD w/ exception, Commercial invoice value |
| 2.2 | Request carrier inspection (if >$2,500 or carrier policy requires) | ❌ No | Claim reference#, Inspection contact, Available time windows |
| 2.3 | Document internal liability: Meridian packing method, bill-of-lading terms, insurance coverage | ⚠️ **Yes – Policy/ERP** | Packing spec (box grade, desiccant, stretch-wrap), BOL terms (FOB), Insurance policy # & limit |
| 2.4 | Assign claim owner; set 48-hr follow-up calendar invite | ❌ No | Claim owner, Due date, Escalation path |

---

### **PHASE 3 – REPLACEMENT FULFILLMENT OPTIONS (Parallel, 0–36 hrs)**
| Option | Feasibility Check | Live System Access Needed? | Exact Data Fields Required |
|--------|-------------------|----------------------------|----------------------------|
| **A. Emergency pick from nearest Meridian DC** | ⚠️ **Yes – Real-time inventory** | **Yes – WMS/ERP** | SKU, Qty needed, DC stock on-hand, Allocated vs. available, Lead time to site |
| **B. Drop-ship from approved vendor (VMI/blanket PO)** | ⚠️ **Yes – Vendor portal/ERP** | **Yes – ERP/Vendor Portal** | Vendor SKU cross-ref, Vendor stock, Vendor lead time, Freight terms, Drop-ship agreement |
| **C. Expedite from Meridian central stock (next-day air)** | ⚠️ **Yes – WMS/ERP** | **Yes – WMS/ERP** | Central stock on-hand, Cut-off time, Carrier cutoff, Freight cost, Account credit hold status |
| **D. Partial shipment: send undamaged lines now, balance ASAP** | ⚠️ **Yes – Order mgmt** | **Yes – ERP/OMS** | Open order lines, Ship-complete flag, Client acceptance of partial, Revised delivery dates |

**Decision Gate (by hr 4):**  
- Confirm fastest viable option(s) with client & internal ops.  
- Lock carrier pickup / vendor dispatch / DC pick wave.  
- Generate new SO/PO for replacements; flag as “CRITICAL – LINE DOWN”.

---

### **PHASE 4 – INTERNAL ESCALATION & ROOT-CAUSE LOOP (Ongoing)**
| Step | Action | Live System Access Needed? | Exact Data Fields Required |
|------|--------|----------------------------|----------------------------|
| 4.1 | Open “Line-Down” incident in CRM/ServiceNow; tag Account Manager, VP Ops, Quality | ⚠️ **Yes – CRM/ITSM** | Incident ID, Severity=1, SLA clock start, Owner, Stakeholder distro list |
| 4.2 | Daily 08:00 stand-up until resolution: carrier claim status, replacement ETA, client comms | ❌ No | Stand-up invite, Status dashboard link |
| 4.3 | Post-mortem (within 5 business days): packing audit, carrier scorecard, PO accuracy, inventory allocation rules | ⚠️ **Yes – ERP/WMS/QMS** | Audit checklist, Carrier KPIs, PO vs. ship variance report, Allocation logic dump |
| 4.4 | Update client SOP: emergency contact tree, safety-stock buffer, advance-ship-notice (ASN) requirements | ⚠️ **Yes – Policy/Docs** | SOP doc ID, Revision log, Client sign-off |

---

### **SUMMARY OF LIVE-SYSTEM GAPS & REQUIRED DATA EXTRACTS**
| System | Missing Live Access | Critical Extracts Needed (CSV/API) |
|--------|---------------------|------------------------------------|
| **ERP / OMS** | Order header/detail, pricing, credit hold, ship-complete flag | `PO#, SO#, SKU, Qty Ord, Qty Ship, Qty BO, Unit Price, Acct Status, ShipCompleteYN` |
| **WMS / Inventory** | Real-time on-hand, allocated, in-transit, lot/serial by DC | `SKU, DC, OnHand, Allocated, Available, InTransit, Lot#, Serial#, BinLoc` |
| **Carrier/TMS** | PRO/BOL tracking, POD images, claim portal | `PRO#, BOL#, Carrier, Status, POD_URL, Claim_Portal_URL` |
| **Vendor Portal / VMI** | Vendor stock, lead time, drop-ship eligibility | `VendorSKU, VendorStock, LeadTimeDays, DropShipYN, FreightTerms` |
| **Policy / QMS** | Packing specs, FOB terms, insurance limits, claim SOP | `PackSpecID, FOB_Term, InsuranceLimit, ClaimSOP_URL` |
| **CRM / ITSM** | Incident tracking, stakeholder comms log | `IncidentID, Severity, Owner, SLA_Deadline, Notes` |

---

### **IMMEDIATE NEXT ACTIONS FOR YOUR TEAM (Next 30 min)**
1. **Pull** the 7 data extracts above for this PO/SO.  
2. **Confirm** Options A–C feasibility with live numbers.  
3. **Dispatch** replacement order on fastest confirmed path.  
4. **Log** “Line-Down” incident; invite VP Ops & Account Manager.  
5. **Send** client a 1-paragraph status email with replacement ETA & claim reference.

*All steps requiring live ERP/WMS/TMS data are flagged ⚠️. Provide the exact fields listed to your integration team for rapid dashboard/build.*
---
Tokens: 375 in / 1857 out | Latency: 51.07s | Est. Cost: $0.000000


### 3. Policy Hallucination Test (`"What is Meridian's return window for opened items?"`)

(desk-env) mydeen0302@DESKTOP-O7NOI15:~/azure-ml/meridian-desk$ python desk.py 
Desk Assistant started (model: nvidia/nemotron-3-ultra-550b-a55b:free, temp: None). Type 'exit' or 'quit' to close.

You: What is Meridian's return window for opened items?

Desk: I don't have live access to Meridian's internal policy documents or ERP system, so I can't confirm the exact return window for opened items.

Once the system is connected, I'll need one of the following to look up the specific policy that applies to your account or order:
- **Account number** (to check your negotiated terms)
- **Order ID / PO number** (to see the policy attached to that transaction)
- **SKU / product category** (some categories—e.g., electrical components, safety gear—have different windows)

In the meantime, the quickest path is to email **returns@meridiansupply.com** with your account number and the order/line items in question; the returns team typically replies within one business day with the applicable window and RMA instructions.
---
Tokens: 263 in / 221 out | Latency: 5.31s | Est. Cost: $0.000000
