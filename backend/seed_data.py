"""
seed_data.py — Generates a realistic 500-vehicle synthetic inventory
with detailed technician/inspector notes and seeds a local SQLite database
with FTS5 support for Hybrid Search (SQL + Semantic RAG) and Copart Knowledge Base.

Run directly: python3 seed_data.py
"""
import sqlite3
import random
import string
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "inventory.db")

# ─── Realistic distributions ───────────────────────────────────────────────────

MAKES_MODELS = {
    "Toyota":   ["Camry", "Corolla", "RAV4", "Highlander", "Tacoma", "4Runner", "Sienna", "Prius"],
    "Honda":    ["Civic", "Accord", "CR-V", "Pilot", "Odyssey", "HR-V", "Ridgeline"],
    "Ford":     ["F-150", "Mustang", "Explorer", "Edge", "Escape", "Ranger", "Expedition", "Focus"],
    "Chevrolet":["Silverado", "Malibu", "Equinox", "Traverse", "Colorado", "Tahoe", "Suburban", "Camaro"],
    "Nissan":   ["Altima", "Sentra", "Rogue", "Pathfinder", "Frontier", "Maxima", "Murano"],
    "BMW":      ["3 Series", "5 Series", "X3", "X5", "7 Series", "X1", "M3"],
    "Mercedes": ["C-Class", "E-Class", "GLE", "GLC", "S-Class", "A-Class"],
    "Jeep":     ["Wrangler", "Cherokee", "Grand Cherokee", "Compass", "Renegade"],
    "Dodge":    ["Charger", "Challenger", "Durango", "Ram 1500"],
    "Hyundai":  ["Elantra", "Sonata", "Tucson", "Santa Fe", "Kona"],
    "Kia":      ["Optima", "Sorento", "Sportage", "Soul", "Telluride"],
    "Volkswagen":["Jetta", "Passat", "Tiguan", "Atlas", "Golf"],
    "Subaru":   ["Outback", "Forester", "Impreza", "Legacy", "Crosstrek"],
    "Audi":     ["A4", "A6", "Q5", "Q7", "Q3"],
    "Tesla":    ["Model 3", "Model Y", "Model S", "Model X"],
    "GMC":      ["Sierra 1500", "Terrain", "Acadia", "Yukon"],
    "Lexus":    ["ES 350", "RX 350", "NX 300", "IS 300"],
    "Mazda":    ["Mazda3", "CX-5", "CX-9", "Mazda6"],
    "Ram":      ["1500", "2500", "ProMaster"],
    "Volvo":    ["XC60", "XC90", "S60", "V60"],
}

BODY_TYPE_MAP = {
    "Camry": "sedan", "Corolla": "sedan", "Civic": "sedan", "Accord": "sedan",
    "Malibu": "sedan", "Altima": "sedan", "Sentra": "sedan", "Maxima": "sedan",
    "Jetta": "sedan", "Passat": "sedan", "Optima": "sedan", "Elantra": "sedan",
    "Sonata": "sedan", "Impreza": "sedan", "Legacy": "sedan", "A4": "sedan",
    "A6": "sedan", "3 Series": "sedan", "5 Series": "sedan", "7 Series": "sedan",
    "C-Class": "sedan", "E-Class": "sedan", "S-Class": "sedan", "Mazda3": "sedan",
    "Mazda6": "sedan", "IS 300": "sedan", "ES 350": "sedan",
    "RAV4": "suv", "Highlander": "suv", "4Runner": "suv", "CR-V": "suv",
    "Pilot": "suv", "HR-V": "suv", "Explorer": "suv", "Edge": "suv",
    "Escape": "suv", "Expedition": "suv", "Equinox": "suv", "Traverse": "suv",
    "Tahoe": "suv", "Suburban": "suv", "Rogue": "suv", "Pathfinder": "suv",
    "Murano": "suv", "X3": "suv", "X5": "suv", "X1": "suv",
    "GLE": "suv", "GLC": "suv", "Wrangler": "suv", "Cherokee": "suv",
    "Grand Cherokee": "suv", "Compass": "suv", "Renegade": "suv",
    "Durango": "suv", "Tucson": "suv", "Santa Fe": "suv", "Kona": "suv",
    "Sorento": "suv", "Sportage": "suv", "Telluride": "suv", "Tiguan": "suv",
    "Atlas": "suv", "Outback": "suv", "Forester": "suv", "Crosstrek": "suv",
    "Q5": "suv", "Q7": "suv", "Q3": "suv", "RX 350": "suv", "NX 300": "suv",
    "CX-5": "suv", "CX-9": "suv", "Terrain": "suv", "Acadia": "suv",
    "Yukon": "suv", "XC60": "suv", "XC90": "suv", "Model Y": "suv",
    "Model X": "suv",
    "F-150": "truck", "Tacoma": "truck", "Ranger": "truck",
    "Colorado": "truck", "Silverado": "truck", "Frontier": "truck",
    "Ridgeline": "truck", "Ram 1500": "truck", "Sierra 1500": "truck",
    "1500": "truck", "2500": "truck",
    "Sienna": "van", "Odyssey": "van", "ProMaster": "van",
    "Mustang": "coupe", "Camaro": "coupe", "Charger": "sedan",
    "Challenger": "coupe", "M3": "sedan",
    "Prius": "hatchback", "Golf": "hatchback", "Soul": "hatchback",
    "A-Class": "hatchback",
    "Model 3": "sedan", "Model S": "sedan",
    "S60": "sedan", "V60": "wagon",
}

COLORS = [
    "White", "Black", "Silver", "Gray", "Blue", "Red", "Green",
    "Brown", "Beige", "Gold", "Orange", "Yellow", "Purple",
]

CONDITIONS = ["run_and_drive", "run_and_drive", "run_and_drive",
              "enhanced_vehicle", "enhanced_vehicle", "stationary", "parts_only"]

DAMAGE_TYPES = [
    "front_end", "front_end", "rear_end", "rear_end",
    "hail", "hail", "flood", "mechanical", "mechanical",
    "rollover", "vandalism", "fire", "minor_dents", "minor_dents",
    "side", "top_roof",
]

LOCATIONS = [
    ("Dallas", "TX"), ("Houston", "TX"), ("San Antonio", "TX"), ("Austin", "TX"),
    ("Los Angeles", "CA"), ("San Diego", "CA"), ("San Jose", "CA"), ("Sacramento", "CA"),
    ("Chicago", "IL"), ("Rockford", "IL"),
    ("Phoenix", "AZ"), ("Tucson", "AZ"),
    ("Jacksonville", "FL"), ("Miami", "FL"), ("Tampa", "FL"), ("Orlando", "FL"),
    ("Atlanta", "GA"), ("Columbus", "GA"),
    ("Charlotte", "NC"), ("Raleigh", "NC"),
    ("Nashville", "TN"), ("Memphis", "TN"),
    ("Las Vegas", "NV"), ("Reno", "NV"),
    ("Seattle", "WA"), ("Spokane", "WA"),
    ("Denver", "CO"), ("Colorado Springs", "CO"),
    ("New York", "NY"), ("Buffalo", "NY"),
    ("Philadelphia", "PA"), ("Pittsburgh", "PA"),
    ("Columbus", "OH"), ("Cleveland", "OH"),
    ("Detroit", "MI"), ("Grand Rapids", "MI"),
    ("Minneapolis", "MN"),
    ("Portland", "OR"),
    ("Salt Lake City", "UT"),
    ("Kansas City", "MO"),
    ("Indianapolis", "IN"),
    ("Louisville", "KY"),
    ("Baltimore", "MD"),
    ("Boston", "MA"),
]

TRANSMISSIONS = ["automatic", "automatic", "automatic", "manual"]

FUEL_TYPES_MAP = {
    "Tesla": "electric",
    "Prius": "hybrid",
    "Model 3": "electric", "Model Y": "electric", "Model S": "electric", "Model X": "electric",
}

TRIMS = {
    "sedan": ["LX", "EX", "SE", "LE", "XLE", "Sport", "Touring", "Limited", "Base"],
    "suv":   ["Sport", "EX-L", "Touring", "XLE", "Limited", "TRD", "Trailhawk", "Platinum"],
    "truck": ["XL", "XLT", "Lariat", "King Ranch", "Platinum", "SR", "SR5", "TRD Pro"],
    "coupe": ["Base", "GT", "GT500", "Hellcat", "Scat Pack", "Premium"],
    "van":   ["LX", "EX", "Touring", "Elite", "Cargo"],
    "hatchback": ["S", "SE", "SEL", "Limited", "Turbo"],
    "wagon": ["T5", "T6", "R-Design", "Momentum"],
    "convertible": ["Base", "Premium", "S", "Sport"],
}

ENGINE_MAP = {
    "sedan": ["2.0L I4", "2.5L I4", "3.5L V6", "2.0L Turbo I4"],
    "suv":   ["2.5L I4", "3.5L V6", "2.0L Turbo I4", "3.6L V6", "5.3L V8"],
    "truck": ["3.5L V6 EcoBoost", "5.0L V8", "2.7L Turbo V6", "6.2L V8", "3.6L V6"],
    "coupe": ["5.0L V8", "3.6L V6", "6.2L Supercharged V8", "2.3L Turbo I4"],
    "van":   ["3.5L V6", "3.6L V6"],
    "hatchback": ["1.5L I4", "2.0L I4", "1.6L Turbo I4"],
    "wagon": ["2.0L Turbo I4", "2.0L I4"],
    "convertible": ["2.0L I4", "3.0L I6"],
}

# ─── Inspector notes templates for semantic search & RAG ─────────────────────

INSPECTOR_NOTE_TEMPLATES = {
    "front_end": [
        "Minor bumper and headlight damage. Radiator is intact, airbags did not deploy. Engine runs smoothly, easy bolt-on fix for a beginner DIY project.",
        "Moderate front-end collision. Bumper, hood, and condenser need replacement. Airbags intact, engine starts and idles without vibration.",
        "Heavy front-end impact. Frame horn bent, steering rack cracked. Airbags deployed. Suitable for parts donor or experienced rebuilder.",
        "Grille and fender scrape from low-speed parking incident. No structural or mechanical damage. Completely drivable.",
    ],
    "rear_end": [
        "Rear bumper cover dented, trunk lid closes and locks properly. Taillights intact. Airbags not deployed, ready to drive.",
        "Impact to tailgate and rear quarter panel. Frame rails straight, suspension unaffected. Clean interior and starts on first crank.",
        "Rear collision pushed exhaust pipe forward. Trunk floor pan buckled slightly. Engine and transmission in excellent condition.",
    ],
    "hail": [
        "Light cosmetic hail dimples on hood and roof panel. No broken glass. Ideal candidate for paintless dent repair (PDR). Drivable condition.",
        "Moderate hail pitting on hood, roof, and trunk. Windshield has minor star crack. Mechanically flawless, clean title history.",
        "Severe hail storm damage across all upper panels. Rear windshield shattered, interior vacuumed. Runs and drives 100%.",
    ],
    "flood": [
        "Freshwater intrusion limited to carpet level. Engine and transmission dry, no water in oil. Electrical accessories tested and working.",
        "Saltwater exposure above seat cushion line. Dashboard display intermittent. ECU needs replacement. Engine turns by hand.",
        "Minor puddle splash into engine intake. MAF sensor replaced, compression test normal. Clean title history before claim.",
    ],
    "minor_dents": [
        "Cosmetic door dings and minor quarter panel scratches. No collision damage, airbags intact. Clean interior, flawless mechanicals.",
        "Scrapes along right passenger doors from guardrail brush. Wheels aligned, runs and drives perfectly. Easy repair.",
    ],
    "mechanical": [
        "Transmission slipping in 3rd gear. Body and frame in mint condition with zero rust or dents. Great project for transmission swap.",
        "Engine head gasket leak, does not start. Electrical and interior in pristine shape. Complete parts intact.",
        "Alternator failed, battery discharged. Jump started and engine runs quiet. Minor wear on brake pads.",
    ],
    "rollover": [
        "Vehicle rolled on dirt embankment. Roof crush on passenger side, glass broken. Drivetrain operational, sold as parts or chassis project.",
    ],
    "vandalism": [
        "Key scratches along both sides and broken passenger window. No mechanical or frame damage. Runs and drives excellent.",
    ],
    "fire": [
        "Engine compartment thermal damage isolated to wiring harness. Cabin and rear of vehicle untouched. Salvage title issued.",
    ],
    "side": [
        "T-bone impact to driver side door. Side curtain airbag deployed. B-pillar dented. Engine and transmission undamaged.",
    ],
    "top_roof": [
        "Tree branch fell on roof panel causing dent. Sunroof glass cracked. Engine runs strong, headlights and front end spotless.",
    ],
}

COPART_POLICIES = [
    {
        "topic": "Run and Drive Condition",
        "keywords": "run and drive, drivable, running, condition",
        "content": "Copart 'Run & Drive' verification means that upon arrival at the facility, the vehicle was verified to start under its own power, engage in gear (forward and reverse), and move under its own power. It does not guarantee roadworthiness or highway safety."
    },
    {
        "topic": "Enhanced Vehicles",
        "keywords": "enhanced vehicle, enhanced, condition",
        "content": "An 'Enhanced Vehicle' means Copart or a seller has rendered special services such as charging the battery, adding fuel, or basic testing. It does not mean the vehicle is in showroom condition, but basic functions have been assessed."
    },
    {
        "topic": "Salvage Title vs Clean Title",
        "keywords": "salvage title, clean title, rebuilt title, title types, laws",
        "content": "A Salvage Title is issued by an insurance company when the cost of repair exceeds a significant percentage (usually 70-80%) of the vehicle's market value. A salvage car cannot be driven on public roads until it is repaired, passes a state safety/theft inspection, and is issued a 'Rebuilt Title'."
    },
    {
        "topic": "Bidding Without a Dealer License",
        "keywords": "dealer license, public buyer, individual bidding, licensing, registration",
        "content": "Many Copart inventory lots are open to public individual buyers without a dealer license, depending on state regulations. For states with strict dealer-only laws (like California for certain salvage titles), individuals can use registered Copart Brokers to place bids."
    },
    {
        "topic": "Paintless Dent Repair (PDR) & Hail Damage",
        "keywords": "paintless dent repair, pdr, hail damage, hail, fix",
        "content": "Hail damaged vehicles frequently offer great value because the damage is purely cosmetic. When the paint surface is unbroken, specialized technicians use Paintless Dent Repair (PDR) rods to massage dents out from behind panels without repainting, saving thousands in repair costs."
    },
    {
        "topic": "Exporting Vehicles Internationally",
        "keywords": "export, international shipping, customs, shipping vehicle",
        "content": "Copart assists international buyers with authorized freight forwarders and customs clearance. Vehicles with 'Certificate of Destruction' or 'Non-Repairable' titles can usually be exported for parts, subject to destination country import rules."
    }
]


def random_vin():
    chars = string.ascii_uppercase.replace("I", "").replace("O", "").replace("Q", "") + string.digits
    return "1" + "".join(random.choices(chars, k=16))


def random_lot():
    return str(random.randint(10_000_000, 99_999_999))


def vehicle_image(make: str, model: str, color: str, year: int) -> str:
    query = f"{year}+{make}+{model}".replace(" ", "+")
    seed = abs(hash(f"{make}{model}{color}{year}")) % 1000
    return f"https://source.unsplash.com/400x260/?car,{query}&sig={seed}"


def generate_inventory(n: int = 500) -> list[dict]:
    records = []
    makes = list(MAKES_MODELS.keys())
    for i in range(n):
        make = random.choice(makes)
        model = random.choice(MAKES_MODELS[make])
        year = random.randint(2010, 2024)
        color = random.choice(COLORS)
        body_type = BODY_TYPE_MAP.get(model, "sedan")
        trim_list = TRIMS.get(body_type, TRIMS["sedan"])
        trim = random.choice(trim_list)
        condition = random.choice(CONDITIONS)
        damage = random.choice(DAMAGE_TYPES)
        city, state = random.choice(LOCATIONS)
        transmission = "automatic" if make in ("Tesla",) else random.choice(TRANSMISSIONS)

        key = model if model in FUEL_TYPES_MAP else make
        if key in FUEL_TYPES_MAP:
            fuel = FUEL_TYPES_MAP[key]
        else:
            fuel = random.choices(["gasoline", "diesel", "hybrid"], weights=[85, 10, 5])[0]

        engine_list = ENGINE_MAP.get(body_type, ENGINE_MAP["sedan"])
        if fuel == "electric":
            engine = "Electric Motor"
        elif fuel == "hybrid":
            engine = "2.5L I4 Hybrid"
        else:
            engine = random.choice(engine_list)

        base_price = {"BMW": 12000, "Mercedes": 13000, "Audi": 11000, "Tesla": 15000,
                      "Lexus": 10000, "Volvo": 9000}.get(make, 6000)
        year_factor = (year - 2010) * 400
        mileage = random.randint(5000, 180000)
        mileage_discount = mileage // 1000 * 30
        damage_discount = {"flood": 3000, "fire": 2500, "rollover": 2000,
                           "parts_only": 4000}.get(damage, 500)
        price = max(800, base_price + year_factor - mileage_discount - damage_discount
                    + random.randint(-1500, 1500))
        price = round(price / 50) * 50

        # Generate realistic inspector notes for semantic search
        note_pool = INSPECTOR_NOTE_TEMPLATES.get(damage, [f"Inspected by technician. Primary damage: {damage.replace('_', ' ')}. Engine turns."])
        notes = random.choice(note_pool)

        records.append({
            "vin": random_vin(),
            "year": year,
            "make": make,
            "model": model,
            "trim": trim,
            "color": color,
            "body_type": body_type,
            "mileage": mileage,
            "price": float(price),
            "damage_type": damage,
            "condition": condition,
            "location_city": city,
            "location_state": state,
            "transmission": transmission,
            "fuel_type": fuel,
            "engine": engine,
            "lot_number": random_lot(),
            "image_url": vehicle_image(make, model, color, year),
            "inspector_notes": notes,
        })
    return records


def seed_database(db_path: str = DB_PATH, n: int = 500):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    c.executescript("""
        DROP TABLE IF EXISTS vehicles_fts;
        DROP TABLE IF EXISTS vehicles;
        DROP TABLE IF EXISTS copart_knowledge;
        DROP TABLE IF EXISTS copart_knowledge_fts;

        CREATE TABLE vehicles (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            vin             TEXT UNIQUE NOT NULL,
            year            INTEGER NOT NULL,
            make            TEXT NOT NULL,
            model           TEXT NOT NULL,
            trim            TEXT,
            color           TEXT NOT NULL,
            body_type       TEXT NOT NULL,
            mileage         INTEGER NOT NULL,
            price           REAL NOT NULL,
            damage_type     TEXT NOT NULL,
            condition       TEXT NOT NULL,
            location_city   TEXT NOT NULL,
            location_state  TEXT NOT NULL,
            transmission    TEXT NOT NULL,
            fuel_type       TEXT NOT NULL,
            engine          TEXT NOT NULL,
            lot_number      TEXT NOT NULL,
            image_url       TEXT NOT NULL,
            inspector_notes TEXT NOT NULL DEFAULT ''
        );

        CREATE INDEX idx_make         ON vehicles(make);
        CREATE INDEX idx_model        ON vehicles(model);
        CREATE INDEX idx_year         ON vehicles(year);
        CREATE INDEX idx_price        ON vehicles(price);
        CREATE INDEX idx_mileage      ON vehicles(mileage);
        CREATE INDEX idx_color        ON vehicles(LOWER(color));
        CREATE INDEX idx_body_type    ON vehicles(body_type);
        CREATE INDEX idx_condition    ON vehicles(condition);
        CREATE INDEX idx_state        ON vehicles(location_state);
        CREATE INDEX idx_fuel         ON vehicles(fuel_type);
        CREATE INDEX idx_transmission ON vehicles(transmission);
        CREATE INDEX idx_damage       ON vehicles(damage_type);

        -- Hybrid FTS5 index for full-text and semantic scoring
        CREATE VIRTUAL TABLE vehicles_fts USING fts5(
            id UNINDEXED,
            make,
            model,
            trim,
            color,
            body_type,
            damage_type,
            condition,
            location_city,
            location_state,
            inspector_notes,
            content='vehicles',
            content_rowid='id'
        );

        -- Copart policy knowledge table for RAG
        CREATE TABLE copart_knowledge (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            topic    TEXT NOT NULL,
            keywords TEXT NOT NULL,
            content  TEXT NOT NULL
        );

        CREATE VIRTUAL TABLE copart_knowledge_fts USING fts5(
            id UNINDEXED,
            topic,
            keywords,
            content,
            content='copart_knowledge',
            content_rowid='id'
        );
    """)

    records = generate_inventory(n)
    cols = ["vin","year","make","model","trim","color","body_type","mileage",
            "price","damage_type","condition","location_city","location_state",
            "transmission","fuel_type","engine","lot_number","image_url","inspector_notes"]
    placeholders = ",".join("?" for _ in cols)
    c.executemany(
        f"INSERT INTO vehicles ({','.join(cols)}) VALUES ({placeholders})",
        [[r[col] for col in cols] for r in records]
    )

    # Populate vehicles FTS index
    c.execute("""
        INSERT INTO vehicles_fts(id, make, model, trim, color, body_type,
                                 damage_type, condition, location_city, location_state, inspector_notes)
        SELECT id, make, model, trim, color, body_type,
               damage_type, condition, location_city, location_state, inspector_notes
        FROM vehicles
    """)

    # Populate Knowledge base
    for item in COPART_POLICIES:
        c.execute("INSERT INTO copart_knowledge (topic, keywords, content) VALUES (?, ?, ?)",
                  (item["topic"], item["keywords"], item["content"]))

    c.execute("""
        INSERT INTO copart_knowledge_fts(id, topic, keywords, content)
        SELECT id, topic, keywords, content FROM copart_knowledge
    """)

    conn.commit()
    conn.close()
    print(f"✅  Seeded {n} vehicles with inspector notes & Copart Knowledge Base into {db_path}")


if __name__ == "__main__":
    seed_database()
