import csv
import json
import random
import sqlite3
from datetime import datetime, timedelta

random.seed(42)  # Reproducible output

# Fixed "today" so statuses are reproducible and consistent with order dates
REFERENCE_DATE = datetime(2026, 11, 17)
BASE_DATE = datetime(2026, 6, 1)
DATE_SPAN_DAYS = (REFERENCE_DATE - BASE_DATE).days  # orders run June 1 -> Nov 17

# ---------------------------------------------------------------------------
# 1. CATEGORIES (FIX #2: sizes, ratings and materials are defined per category
#    and per item, so every combination is realistic)
#    code: (category name, sizes, ratings, {item: [valid materials]})
# ---------------------------------------------------------------------------
CATEGORIES = {
    "VLV": ("Valves & Fittings",
            ["1/4-inch", "1/2-inch", "3/4-inch", "1-inch", "2-inch"],
            ["150 PSI", "300 PSI", "1000 PSI", "3000 PSI"],
            {
                "Ball Valve": ["316 Stainless Steel", "Brass", "Schedule 80 PVC"],
                "Gate Valve": ["Carbon Steel", "Brass", "Cast Iron"],
                "Check Valve": ["316 Stainless Steel", "Brass", "Schedule 80 PVC"],
                "Butterfly Valve": ["Carbon Steel", "316 Stainless Steel", "Ductile Iron"],
                "Needle Valve": ["316 Stainless Steel", "Brass"],
                "Pressure Relief Valve": ["Brass", "316 Stainless Steel", "Carbon Steel"],
                "Elbow Fitting": ["316 Stainless Steel", "Brass", "Schedule 80 PVC", "Carbon Steel"],
                "Tee Coupling": ["316 Stainless Steel", "Brass", "Schedule 80 PVC", "Carbon Steel"],
            }),
    "PPE": ("Safety & PPE",
            ["Medium", "Large", "X-Large", "Universal"],
            ["OSHA Compliant", "ANSI Certified", "CE Certified"],
            {
                "Nitrile Gloves": ["Reinforced Nitrile"],
                "Safety Goggles": ["Polycarbonate"],
                "Hard Hat": ["High-Density Polyethylene"],
                "Steel-Toe Boots": ["Full-Grain Leather"],
                "Respirator Mask": ["Silicone"],
                "Ear Muffs": ["ABS Plastic"],
                "High-Vis Vest": ["Polyester Mesh"],
                "Chemical Apron": ["PVC-Coated Fabric", "Reinforced Nitrile"],
            }),
    "FST": ("Fasteners",
            ["M6", "M8", "M10", "M12", "1/4-inch", "1/2-inch"],
            ["Grade 5", "Grade 8", "A4-70 Marine Grade"],
            {
                "Hex Bolt": ["Zinc-Plated Steel", "316 Stainless Steel", "Alloy Steel"],
                "Lock Nut": ["Zinc-Plated Steel", "316 Stainless Steel"],
                "Flat Washer": ["Zinc-Plated Steel", "316 Stainless Steel"],
                "Socket Cap Screw": ["Alloy Steel", "316 Stainless Steel"],
                "Concrete Anchor": ["Zinc-Plated Steel", "316 Stainless Steel"],
                "Threaded Rod": ["Carbon Steel", "316 Stainless Steel"],
                "Spring Pin": ["Carbon Steel", "316 Stainless Steel"],
                "Blind Rivet": ["Aluminum", "Steel"],
            }),
    "TLS": ("Power & Hand Tools",
            ["Compact", "Standard", "Heavy-Duty", "Professional Kit"],
            ["UL Listed", "CE Certified", "Industrial Grade", "IP54 Dust Protected"],
            {
                "Impact Wrench": ["Chrome Vanadium"],
                "Cordless Drill": ["Glass-Filled Nylon"],
                "Angle Grinder": ["Die-Cast Aluminum"],
                "Torque Wrench": ["Chrome Vanadium"],
                "Digital Caliper": ["Hardened Stainless Steel"],
                "Pipe Cutter": ["Hardened Steel"],
                "Crimping Tool": ["Forged Steel"],
                "Heat Gun": ["Glass-Filled Nylon"],
            }),
    "ELC": ("Electrical",
            ["24V DC", "120V", "240V", "480V"],
            ["UL Listed", "IP67 Waterproof", "CE Certified", "NEMA 4X"],
            {
                "Circuit Breaker": ["Thermoplastic"],
                "Conduit Pipe": ["Galvanized Steel", "Schedule 80 PVC", "Aluminum"],
                "Terminal Block": ["Nylon 66"],
                "Relay Switch": ["Thermoset Resin"],
                "Control Transformer": ["Copper-Wound"],
                "Junction Box": ["Galvanized Steel", "Polycarbonate"],
                "Proximity Sensor": ["316 Stainless Steel", "Nickel-Plated Brass"],
                "Cable Gland": ["Nickel-Plated Brass", "Nylon"],
            }),
    "HYD": ("Hydraulics",
            ["1/4-inch", "3/8-inch", "1/2-inch", "3/4-inch", "1-inch"],
            ["3000 PSI", "5000 PSI", "6000 PSI", "ISO 4413 Compliant"],
            {
                "Hydraulic Hose": ["Braided Synthetic Rubber"],
                "Quick Disconnect Coupler": ["Carbon Steel", "Brass"],
                "Gear Pump": ["Cast Iron", "Anodized Aluminum"],
                "Hydraulic Cylinder": ["Chrome-Plated Steel"],
                "Pressure Gauge": ["316 Stainless Steel"],
                "Oil Filter Element": ["Cellulose Fiber", "Glass Fiber"],
                "Manifold Block": ["Anodized Aluminum", "Carbon Steel"],
                "Seal Kit": ["Viton", "Polyurethane", "Nitrile Rubber"],
            }),
    "ABR": ("Abrasives",
            ["60-Grit", "80-Grit", "120-Grit", "4-1/2-inch", "6-inch"],
            ["ANSI B7.1 Compliant", "Max 12,000 RPM", "Industrial Grade"],
            {
                "Cut-Off Wheel": ["Aluminum Oxide", "Zirconia Alumina"],
                "Flap Disc": ["Zirconia Alumina", "Ceramic"],
                "Sanding Belt": ["Aluminum Oxide", "Silicon Carbide"],
                "Grinding Wheel": ["Aluminum Oxide", "Silicon Carbide"],
                "Wire Cup Brush": ["Carbon Steel Wire", "Stainless Steel Wire"],
                "Polishing Pad": ["Wool", "Foam"],
                "Deburring Burr": ["Tungsten Carbide"],
                "Emery Cloth": ["Emery"],
            }),
    "FAC": ("Facility & Janitorial",
            ["Standard", "Heavy-Duty", "Bulk Pack", "Industrial Size"],
            ["OSHA Compliant", "NFPA Compliant", "Industrial Grade", "Biodegradable"],
            {
                "Industrial Degreaser": ["Water-Based Formula", "Solvent-Based Formula"],
                "Spill Containment Kit": ["Polypropylene"],
                "Pallet Jack Wheel": ["Polyurethane", "Nylon"],
                "Floor Marking Tape": ["Vinyl"],
                "Absorbent Pads": ["Polypropylene"],
                "Safety Cabinet": ["Powder-Coated Steel"],
                "Drum Pump": ["Polypropylene", "316 Stainless Steel"],
                "LED High-Bay Light": ["Die-Cast Aluminum"],
            }),
}

CUSTOMERS = [
    "Apex Fabrication", "Ironclad Construction", "Vanguard Logistics", "Sterling Manufacturing",
    "Titan Heavy Industries", "BlueRidge Energy", "Cascadia Pulp & Paper", "Metro Rail Maintenance",
    "Summit Aerospace Parts", "Great Lakes Marine", "Keystone Foundry", "Frontier Mining Supply",
    "Pacific Cold Storage", "Heartland Ag Equipment", "Delta Chemical Works", "Redwood Timber Co."
]
CARRIERS = ["FedEx Freight", "UPS Supply Chain", "XPO Logistics", "Old Dominion", "Estes Express"]


# ---------------------------------------------------------------------------
# 2. GENERATE catalog.csv (200 PRODUCTS)
# ---------------------------------------------------------------------------
catalog = []
cat_codes = list(CATEGORIES.keys())

for i in range(200):
    cat_code = cat_codes[i % len(cat_codes)]
    cat_name, sizes, ratings, items = CATEGORIES[cat_code]
    item_names = list(items.keys())
    item_base = item_names[(i // len(cat_codes)) % len(item_names)]

    mat = random.choice(items[item_base])      # material valid for THIS item
    size = random.choice(sizes)                # size valid for THIS category
    rating = random.choice(ratings)            # rating valid for THIS category

    sku = f"MS-{cat_code}-{i + 1:04d}"
    name = f"{item_base}, {mat} ({size})"
    unit_price = round(random.uniform(8.50, 480.00), 2)
    stock = random.randint(0, 850)
    specs = f"Material: {mat}; Size/Spec: {size}; Rating: {rating}; Category: {cat_name}"

    catalog.append({
        "sku": sku, "name": name, "category": cat_name,
        "unit_price": unit_price, "stock": stock, "specs": specs
    })

with open("catalog.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["sku", "name", "category", "unit_price", "stock", "specs"])
    writer.writeheader()
    writer.writerows(catalog)


# ---------------------------------------------------------------------------
# 3. BUILD 500 ORDERS IN MEMORY
#    FIX #3: status depends on the order's age
# ---------------------------------------------------------------------------
def pick_status(age_days):
    if age_days > 21:       # old orders: almost all delivered
        return random.choices(["delivered", "cancelled"], weights=[92, 8])[0]
    if age_days > 7:        # mid-age orders: mostly delivered or in transit
        return random.choices(["delivered", "shipped", "cancelled"], weights=[60, 35, 5])[0]
    # last week: still being processed or just shipped
    return random.choices(["processing", "shipped", "cancelled"], weights=[50, 40, 10])[0]


orders = []
for idx in range(500):
    order_date = BASE_DATE + timedelta(days=random.randint(0, DATE_SPAN_DAYS))
    age_days = (REFERENCE_DATE - order_date).days

    line_items = []
    for prod in random.sample(catalog, random.randint(1, 4)):
        line_items.append({
            "sku": prod["sku"],
            "name": prod["name"],
            "qty": random.randint(2, 50),
            "unit_price": prod["unit_price"],   # correct catalog price for now
        })

    orders.append({
        "id": f"MS-{10001 + idx}",
        "customer": random.choice(CUSTOMERS),
        "line_items": line_items,
        "status": pick_status(age_days),
        "order_date": order_date.strftime("%Y-%m-%d"),
        "carrier": random.choice(CARRIERS),
    })


# ---------------------------------------------------------------------------
# 4. PLANT 10 PRICING MISMATCHES
#    FIX #4: only on non-cancelled orders (cancelled orders were never billed)
# ---------------------------------------------------------------------------
catalog_price = {p["sku"]: p["unit_price"] for p in catalog}
eligible = [i for i, o in enumerate(orders) if o["status"] != "cancelled"]
mismatched_indices = random.sample(eligible, 10)

cheat_sheet = []
for idx in mismatched_indices:
    order = orders[idx]
    item = order["line_items"][0]                       # corrupt the first line
    true_price = catalog_price[item["sku"]]
    item["unit_price"] = round(true_price * random.choice([0.75, 1.25]), 2)

    cheat_sheet.append({
        "order_id": order["id"],
        "customer": order["customer"],
        "status": order["status"],
        "order_date": order["order_date"],
        "sku": item["sku"],
        "catalog_unit_price": true_price,
        "billed_unit_price": item["unit_price"],
        "qty": item["qty"],
        "expected_line_total": round(true_price * item["qty"], 2),
        "billed_line_total": round(item["unit_price"] * item["qty"], 2),
        "difference": round((item["unit_price"] - true_price) * item["qty"], 2),
    })


# ---------------------------------------------------------------------------
# 5. WRITE orders.db (totals computed AFTER mismatches, so each order is
#    internally consistent and the error only shows against the catalog)
# ---------------------------------------------------------------------------
conn = sqlite3.connect("orders.db")
cur = conn.cursor()
cur.execute("DROP TABLE IF EXISTS orders")
cur.execute("""
CREATE TABLE orders (
    id TEXT PRIMARY KEY,
    customer TEXT,
    line_items TEXT,
    status TEXT,
    order_date TEXT,
    carrier TEXT,
    total REAL
)
""")

for o in orders:
    total = round(sum(round(li["unit_price"] * li["qty"], 2) for li in o["line_items"]), 2)
    cur.execute(
        "INSERT INTO orders (id, customer, line_items, status, order_date, carrier, total) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (o["id"], o["customer"], json.dumps(o["line_items"]), o["status"],
         o["order_date"], o["carrier"], total)
    )

conn.commit()
conn.close()

with open("audit_cheat_sheet.json", "w", encoding="utf-8") as f:
    json.dump(cheat_sheet, f, indent=2)

print("Done! Generated catalog.csv (200), orders.db (500), and audit_cheat_sheet.json (10 traps).")