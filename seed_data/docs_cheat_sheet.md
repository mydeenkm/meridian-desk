# Answer key for policies/ and emails/ (keep hidden during the challenge)

Reference date: **Tue 17 Nov 2026**. Order data comes from `orders.db` and `catalog.csv`.

## 1. The planted policy contradiction

| | `returns-policy.md` | `returns-policy-v2.md` |
|---|---|---|
| Document ID | POL-RET-01 v1.3 | POL-RET-01 v2.0 |
| Effective date | 2026-03-01 | **2026-10-01** |
| Return window | 30 days | **21 days** |
| Restocking fee | 15% | **20%** |

The v2 document does not say it replaces v1. It only says it applies to return requests received on or after 2026-10-01. All return emails are dated November, so **v2 governs**. A correct answer uses v2, and the effective date is the tie-breaker.

Other policies have no deliberate contradictions. The documents agree on the rest.

## 2. Messy emails (6)

| Email | What makes it messy |
|---|---|
| 02 | Product described in words only. It uniquely matches **MS-VLV-0193** (316 SS ball valve, 2-inch, $418.56) |
| 04 | Words only, and ambiguous: degreaser = MS-FAC-0136 (Industrial Size) or MS-FAC-0008 (Bulk Pack); drum pump has 3 candidates. Asks for FedEx hazmat and delivery by Friday. Ask for clarification |
| 10 | Multiple intents: status, add-on item, return terms. "Drum pumps we got last time" = MS-FAC-0056 |
| 11 | Forwarded chain, two orders, an expedite request, and a warranty question |
| 23 | No order number, vague product ("glass fiber oil filters, 3/8" = MS-HYD-0046), three separate questions |
| 27 | **Wrong order number** (MS-10650 does not exist). Items match **MS-10365** (Vanguard Logistics, 19 Oct) |
| 29 | Multiple intents, plus a callback and terms question |

## 3. Expected answers per email

| # | Customer | Type | Expected outcome |
|---|---|---|---|
| 01 | Ironclad | Order | Gloves 200 x $56.83 = $11,366.00, 10% bulk = $10,229.40. Ear muffs 40 x $236.99 = $9,479.60, 6% bulk = $8,910.82. Discount must be requested. Freight free (over $5,000) |
| 02 | Apex | Order (words) | MS-VLV-0193 x 20 = $8,371.20; 3% bulk = $8,120.06. Stock 450 |
| 03 | Frontier | Reorder MS-10061 x2 | MS-VLV-0065 x 86 ($11,774.26), MS-HYD-0014 x 64 ($18,925.44). 6% bulk if requested |
| 04 | Heartland | Messy order | Needs clarification. Solvent degreaser is hazmat: no FedEx, ground only, $75 fee, +3 business days, so not by Friday |
| 05 | Delta | Hazmat order | Air freight refused. Ground only via XPO or Old Dominion, $75 hazmat fee, +3 days. 60 x $362.35 = $21,741.00 |
| 06 | Keystone | Quote + terms | 500 units is over 250, so custom quote. Stock of MS-FST-0003 is only 30, so backorder. Net 60 not offered (max Net 45, Tier C) |
| 07 | Pacific | Status | MS-10225 processing, placed 16 Nov, ships within 2 business days (FedEx Freight) |
| 08 | Summit | Tracking | MS-10333 shipped 17 Nov, FedEx Freight. Tracking number is not in the data, so it cannot be given |
| 09 | Metro Rail | Status + liftgate | MS-10420 shipped 16 Nov, FedEx Freight. Liftgate must be requested before shipment, so not possible now ($45 normally) |
| 10 | Titan | Messy | MS-10393 processing. Add-on pumps need a change request (no policy covers it). Return terms = v2 (21 days, 20%) |
| 11 | BlueRidge | Messy | MS-10346 processing since 10 Nov (overdue vs 2-day processing). MS-10111 shipped 15 Nov, Estes. Seal kits are 90-day consumables |
| 12 | Cascadia | Complaint | MS-10480 shows cancelled. Reason not in data (customer or credit hold). Escalate, do not guess |
| 13 | Sterling | Wrong item | Arrived 11 Nov, reported 17 Nov = 4 business days, **within** the 5-day window. Replacement, MS pays freight |
| 14 | Heartland | Damage | Arrived 9 Nov, reported 17 Nov = 6 business days, **outside** the window. Case-by-case review |
| 15 | Great Lakes | Delay | MS-10013 shipped 13 Nov, only 2 business days ago. Transit is 3 to 7 days, so **not late**. No freight refund. Customer threatens to leave, so Account Manager |
| 16 | Vanguard | Price dispute | Invoice $422.82 matches catalog. No written quote reference, so verbal quote not honored. Within 30-day window |
| 17 | Titan | Return | Delivered 2 Nov, request 14 Nov = 12 days, eligible. 10 x $206.16 = $2,061.60, v2 fee 20% = $412.32, **credit $1,649.28** (v1 would wrongly give $1,752.36) |
| 18 | Redwood | Return | Arrived 22 Oct, now day 26. **Not eligible under v2 (21 days)**. v1 would allow it ($5,672.60 credit), which is the trap |
| 19 | Great Lakes | Return | **Hazmat, not returnable**, and also past 21 days |
| 20 | Apex | Return | Delivered 30 Oct, now day 18, eligible. 6 x $301.46 = $1,808.76, 20% = $361.75, **credit $1,447.01** |
| 21 | Metro Rail | Warranty | Tools have 12 months, so covered. Report within 30 days. Replacement or credit, no restocking fee |
| 22 | Summit | Credit | Tier C fits (over 24 months): limit up to $150,000, Net 45. Finance review 5 to 7 business days |
| 23 | Redwood | Messy | MS-HYD-0046 x 30 = $6,798.90, 6% bulk if requested. Late fee cannot be verified from the data. Freight under $1,000 = $65 |
| 24 | Delta | Status | MS-10445 shipped 15 Nov, XPO Logistics, 3 to 7 business days |
| 25 | Pacific | Stock | MS-TLS-0092 has stock 0, so backorder 10 to 15 business days. Same-name alternatives: MS-TLS-0028 ($290.90), MS-TLS-0156 ($271.63) |
| 26 | Keystone | Cancel | MS-10431 placed today, in processing within 24 hours, so free cancellation |
| 27 | Vanguard | Messy status | MS-10650 does not exist. Likely MS-10365 (delivered, 19 Oct) |
| 28 | Ironclad | Freight | $3,500 ground = $120. Expedited +25% = $150 |
| 29 | Great Lakes | Messy | MS-10304 shipped 13 Nov, XPO. 30 x $280.57 = $8,417.10; 6% bulk = $7,912.07 if requested. No record of a "same discount as before". Callback cannot be verified |
| 30 | Cascadia | Angry status | MS-10086 shipped 11 Nov, UPS Supply Chain, 4 business days ago, still within transit window. Tracking number is not in the data |

## 4. Known quirks in the data
- Some existing solvent-degreaser orders in `orders.db` show FedEx Freight or UPS as carrier, even though policy says hazmat can only go with XPO or Old Dominion. Carriers are random in the generator.
- Some catalog products share a name but have different SKUs and prices (for example three "Torque Wrench, Chrome Vanadium (Standard)").
