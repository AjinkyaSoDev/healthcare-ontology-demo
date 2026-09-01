"""Synthetic data generator for the Constanto Compounding Ontology demo.

Domain: pharmaceutical compounding / personalized medicine (Constanto's business).
Produces a connected set of CSV tables that map to entity types and relationships in
a Microsoft Fabric Digital Twin Builder ontology.

The data is intentionally *connected* so the demo can show end-to-end traceability:
  Patient -> Prescription -> Formula -> (BOM) Ingredient -> RawMaterialLot -> Supplier
  Formula -> Batch -> QualityTest / StabilityReading
  Batch  -> Pharmacy(site) -> Cleanroom -> CleanroomSensorReading (time series)

A deliberate quality excursion is seeded (a bad raw-material lot) so the demo can walk
the graph from a failed batch back to the supplier and forward to affected patients.

Run:  python src/generate_data.py
Output: data/*.csv
"""
from __future__ import annotations

import csv
import os
import random
from datetime import datetime, timedelta, date

random.seed(2026)

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
os.makedirs(OUT, exist_ok=True)


def write(name: str, header: list[str], rows: list[list]) -> None:
    path = os.path.join(OUT, name)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
    print(f"{name}: {len(rows)} rows")


# --------------------------------------------------------------------------- #
# Reference / dimension entities
# --------------------------------------------------------------------------- #
SITES = [
    ("SITE-01", "Constanto Compounding Rotterdam", "Rotterdam, NL", "NL-GMP-4471"),
    ("SITE-02", "Constanto Sterile Services Barcelona", "Barcelona, ES", "ES-GMP-2290"),
    ("SITE-03", "Constanto Compounding Wichita", "Wichita, US", "US-503B-1187"),
]

CLEANROOMS = [
    ("ROOM-01", "SITE-01", "Non-sterile Suite A", "ISO 8"),
    ("ROOM-02", "SITE-01", "Sterile Suite B", "ISO 7"),
    ("ROOM-03", "SITE-02", "Sterile Suite A", "ISO 7"),
    ("ROOM-04", "SITE-03", "Non-sterile Suite A", "ISO 8"),
]

EQUIPMENT = [
    ("EQ-01", "SITE-01", "Unguator Ointment Mill", "Mixing"),
    ("EQ-02", "SITE-01", "Capsule Filling Machine CFM-100", "Encapsulation"),
    ("EQ-03", "SITE-02", "Laminar Flow Hood LFH-7", "Aseptic"),
    ("EQ-04", "SITE-02", "Sterile Filtration Unit SFU-3", "Filtration"),
    ("EQ-05", "SITE-03", "Ointment Mill OM-2", "Mixing"),
]

SUPPLIERS = [
    ("SUP-01", "PharmaRaw GmbH", "Germany", "Yes"),
    ("SUP-02", "Actives Iberia SA", "Spain", "Yes"),
    ("SUP-03", "GlobalAPI Trading", "India", "Yes"),
    ("SUP-04", "Excipient Partners BV", "Netherlands", "Yes"),
    ("SUP-05", "LowCost Chem Ltd", "China", "No"),   # non-GMP -> risk story
]

# Ingredients: APIs + excipients
INGREDIENTS = [
    ("ING-01", "Estradiol", "API", "50-28-2", "H360", "hormone"),
    ("ING-02", "Progesterone", "API", "57-83-0", "H360", "hormone"),
    ("ING-03", "Testosterone", "API", "58-22-0", "H360", "hormone"),
    ("ING-04", "Ketamine HCl", "API", "1867-66-9", "H302", "analgesic"),
    ("ING-05", "Gabapentin", "API", "60142-96-3", "H302", "analgesic"),
    ("ING-06", "Baclofen", "API", "1134-47-0", "H302", "muscle-relaxant"),
    ("ING-07", "Naltrexone HCl", "API", "16676-29-2", "H302", "LDN"),
    ("ING-08", "Tacrolimus", "API", "104987-11-3", "H302", "immunomodulator"),
    ("ING-09", "Constanto PCCA Lipoderm", "Excipient", "NA", "None", "transdermal-base"),
    ("ING-10", "VersaPro Cream Base", "Excipient", "NA", "None", "cream-base"),
    ("ING-11", "SyrSpend SF pH4", "Excipient", "NA", "None", "suspension-base"),
    ("ING-12", "Microcrystalline Cellulose", "Excipient", "9004-34-6", "None", "filler"),
    ("ING-13", "Purified Water", "Excipient", "7732-18-5", "None", "solvent"),
]

# Master formulas (compounded preparations)
FORMULAS = [
    ("FORM-01", "Estradiol/Progesterone 1mg/100mg Transdermal Cream", "Transdermal Cream", "Topical", "HRT"),
    ("FORM-02", "Testosterone 2% Transdermal Cream", "Transdermal Cream", "Topical", "HRT"),
    ("FORM-03", "Ketamine 10% Topical Cream", "Topical Cream", "Topical", "Pain"),
    ("FORM-04", "Gabapentin/Baclofen 6%/2% Cream", "Topical Cream", "Topical", "Pain"),
    ("FORM-05", "Low Dose Naltrexone 4.5mg Capsule", "Capsule", "Oral", "Immunology"),
    ("FORM-06", "Tacrolimus 0.03% Ophthalmic Suspension", "Suspension", "Ophthalmic", "Immunology"),
    ("FORM-07", "Gabapentin 100mg/mL Oral Suspension", "Suspension", "Oral", "Pain"),
]

# Bill of materials: formula -> ingredient
FORMULA_BOM = [
    # FORM-01
    ("FORM-01", "ING-01", 1.0, "mg", "API"),
    ("FORM-01", "ING-02", 100.0, "mg", "API"),
    ("FORM-01", "ING-09", 30.0, "g", "Base"),
    # FORM-02
    ("FORM-02", "ING-03", 2.0, "g", "API"),
    ("FORM-02", "ING-09", 98.0, "g", "Base"),
    # FORM-03
    ("FORM-03", "ING-04", 10.0, "g", "API"),
    ("FORM-03", "ING-10", 90.0, "g", "Base"),
    # FORM-04
    ("FORM-04", "ING-05", 6.0, "g", "API"),
    ("FORM-04", "ING-06", 2.0, "g", "API"),
    ("FORM-04", "ING-10", 92.0, "g", "Base"),
    # FORM-05
    ("FORM-05", "ING-07", 4.5, "mg", "API"),
    ("FORM-05", "ING-12", 200.0, "mg", "Filler"),
    # FORM-06
    ("FORM-06", "ING-08", 0.03, "g", "API"),
    ("FORM-06", "ING-11", 100.0, "mL", "Base"),
    # FORM-07
    ("FORM-07", "ING-05", 10.0, "g", "API"),
    ("FORM-07", "ING-11", 100.0, "mL", "Base"),
]

OPERATORS = [
    ("OP-01", "M. van Dijk", "Pharmacist", "SITE-01"),
    ("OP-02", "S. Jansen", "Technician", "SITE-01"),
    ("OP-03", "L. Garcia", "Pharmacist", "SITE-02"),
    ("OP-04", "A. Ferrer", "Technician", "SITE-02"),
    ("OP-05", "J. Miller", "Pharmacist", "SITE-03"),
]

PRESCRIBERS = [
    ("DR-01", "Dr. E. Bakker", "Endocrinology", "Rotterdam Medical Center"),
    ("DR-02", "Dr. P. Costa", "Pain Management", "Barcelona Health Clinic"),
    ("DR-03", "Dr. R. Smith", "Rheumatology", "Wichita Care Group"),
    ("DR-04", "Dr. N. de Vries", "Dermatology", "Rotterdam Skin Institute"),
    ("DR-05", "Dr. M. Lopez", "Ophthalmology", "Barcelona Eye Clinic"),
]


def gen_patients(n=60):
    regions = ["Rotterdam, NL", "Barcelona, ES", "Wichita, US", "Amsterdam, NL", "Madrid, ES"]
    allergies = ["None", "None", "None", "Penicillin", "Peanut", "Sulfa", "Latex"]
    rows = []
    for i in range(1, n + 1):
        rows.append([
            f"PAT-{i:04d}",
            f"Patient {i:04d}",                      # synthetic, no real PII
            random.randint(1945, 2010),              # birth year
            round(random.uniform(50, 105), 1),       # weight kg
            random.choice(allergies),
            random.choice(regions),
        ])
    return rows


def main():
    write("site.csv", ["site_id", "name", "location", "license"], [list(s) for s in SITES])
    write("cleanroom.csv", ["room_id", "site_id", "name", "iso_class"],
          [list(c) for c in CLEANROOMS])
    write("equipment.csv", ["equipment_id", "site_id", "name", "type"],
          [list(e) for e in EQUIPMENT])
    write("supplier.csv", ["supplier_id", "name", "country", "gmp_certified"],
          [list(s) for s in SUPPLIERS])
    write("ingredient.csv",
          ["ingredient_id", "name", "type", "cas_number", "hazard_class", "category"],
          [list(i) for i in INGREDIENTS])
    write("formula.csv",
          ["formula_id", "name", "dosage_form", "route", "therapeutic_area"],
          [list(f) for f in FORMULAS])
    write("formula_ingredient.csv",
          ["formula_id", "ingredient_id", "quantity", "unit", "function"],
          [list(b) for b in FORMULA_BOM])
    write("operator.csv", ["operator_id", "name", "role", "site_id"],
          [list(o) for o in OPERATORS])
    write("prescriber.csv", ["prescriber_id", "name", "specialty", "clinic"],
          [list(p) for p in PRESCRIBERS])

    patients = gen_patients(60)
    write("patient.csv",
          ["patient_id", "display_name", "birth_year", "weight_kg", "allergies", "region"],
          patients)

    # --- Raw material lots (one+ per ingredient) with a seeded bad lot ---
    lots = []
    lot_by_ing: dict[str, list[str]] = {}
    lot_seq = 1
    base_day = date(2025, 1, 5)
    BAD_LOT = "LOT-0043"          # seeded out-of-spec lot
    for ing in INGREDIENTS:
        ing_id = ing[0]
        n_lots = random.randint(1, 3)
        for _ in range(n_lots):
            lot_id = f"LOT-{lot_seq:04d}"
            supplier = random.choice(SUPPLIERS)[0]
            # force the bad lot to come from the non-GMP supplier for a clean story
            if lot_id == BAD_LOT:
                supplier = "SUP-05"
                ing_id = "ING-04"   # Ketamine HCl -> used in FORM-03
            recv = base_day + timedelta(days=random.randint(0, 120))
            expiry = recv + timedelta(days=random.randint(365, 900))
            qc = "Released"
            if lot_id == BAD_LOT:
                qc = "Quarantined"
            lots.append([lot_id, ing_id, supplier, recv.isoformat(),
                         expiry.isoformat(), qc, random.randint(50, 500)])
            lot_by_ing.setdefault(ing_id, []).append(lot_id)
            lot_seq += 1
    # ensure the bad lot exists even if loop randomness skipped ING-04 addition
    if not any(r[0] == BAD_LOT for r in lots):
        lots.append([BAD_LOT, "ING-04", "SUP-05", "2025-02-10",
                     "2026-08-10", "Quarantined", 120])
        lot_by_ing.setdefault("ING-04", []).append(BAD_LOT)
    write("raw_material_lot.csv",
          ["lot_id", "ingredient_id", "supplier_id", "received_date",
           "expiry_date", "qc_status", "quantity_g"], lots)

    # --- Batches (production orders) ---
    batches = []
    batch_lot_links = []
    batch_seq = 1
    for _ in range(120):
        form = random.choice(FORMULAS)
        form_id = form[0]
        site = random.choice(SITES)[0]
        ops = [o for o in OPERATORS if o[3] == site] or OPERATORS
        op = random.choice(ops)[0]
        eqs = [e for e in EQUIPMENT if e[1] == site] or EQUIPMENT
        eq = random.choice(eqs)[0]
        comp_day = base_day + timedelta(days=random.randint(30, 210))
        expiry = comp_day + timedelta(days=random.randint(90, 365))
        batch_id = f"BATCH-{batch_seq:04d}"
        status = "Released"
        # link the raw material lots used (from the formula BOM)
        used_bad = False
        for bom in FORMULA_BOM:
            if bom[0] != form_id:
                continue
            ing_id = bom[1]
            lots_for = lot_by_ing.get(ing_id, [])
            if not lots_for:
                continue
            chosen = random.choice(lots_for)
            if chosen == BAD_LOT:
                used_bad = True
            batch_lot_links.append([batch_id, chosen, ing_id])
        if used_bad:
            status = "Recalled"     # batches using the bad lot are recalled
        batches.append([batch_id, form_id, site, op, eq,
                        comp_day.isoformat(), expiry.isoformat(),
                        random.randint(20, 200), status])
        batch_seq += 1
    write("batch.csv",
          ["batch_id", "formula_id", "site_id", "operator_id", "equipment_id",
           "compounded_date", "expiry_date", "quantity_units", "status"], batches)
    write("batch_raw_material_lot.csv",
          ["batch_id", "lot_id", "ingredient_id"], batch_lot_links)

    # --- Prescriptions (link patients -> formulas), some fulfilled by recalled batches ---
    recalled_batches = [b[0] for b in batches if b[8] == "Recalled"]
    prescriptions = []
    for i in range(1, 141):
        pat = random.choice(patients)[0]
        presc = random.choice(PRESCRIBERS)[0]
        form = random.choice(FORMULAS)[0]
        # some prescriptions were dispensed from a matching batch
        matching = [b for b in batches if b[1] == form]
        batch_id = random.choice(matching)[0] if matching and random.random() < 0.8 else ""
        pdate = base_day + timedelta(days=random.randint(40, 220))
        prescriptions.append([
            f"RX-{i:04d}", pat, presc, form, batch_id,
            pdate.isoformat(),
            random.choice(["Once daily", "Twice daily", "Every 8h", "As needed"]),
            random.choice(["Active", "Active", "Completed"]),
        ])
    write("prescription.csv",
          ["prescription_id", "patient_id", "prescriber_id", "formula_id",
           "dispensed_batch_id", "prescription_date", "frequency", "status"],
          prescriptions)

    # --- Quality tests per batch ---
    qtests = []
    qseq = 1
    test_types = [("Assay", 95.0, 105.0), ("pH", 4.0, 7.0),
                  ("Sterility", 1.0, 1.0), ("Content Uniformity", 90.0, 110.0)]
    bad_batches = set(recalled_batches)
    for b in batches:
        batch_id = b[0]
        for tt, lo, hi in random.sample(test_types, k=random.randint(2, 3)):
            if tt == "Sterility":
                result = 1.0
                pf = "Pass"
            else:
                mid = (lo + hi) / 2
                result = round(random.uniform(lo + 0.5, hi - 0.5), 2)
                pf = "Pass"
                if batch_id in bad_batches and tt == "Assay":
                    result = round(random.uniform(80.0, 89.0), 2)  # out of spec
                    pf = "Fail"
            qtests.append([f"QC-{qseq:05d}", batch_id, tt, result, lo, hi, pf,
                           b[5]])  # test date = compounded date (approx)
            qseq += 1
    write("quality_test.csv",
          ["test_id", "batch_id", "test_type", "result", "spec_min", "spec_max",
           "pass_fail", "test_date"], qtests)

    # --- Time series: cleanroom sensor readings (hourly, ~10 days per room) ---
    cs = []
    start = datetime(2025, 3, 1, 0, 0, 0)
    for room in CLEANROOMS:
        room_id = room[0]
        iso = room[3]
        base_particle = 3520 if iso == "ISO 7" else 352000  # ISO limits (0.5um)
        for hour in range(0, 24 * 10):
            ts = start + timedelta(hours=hour)
            temp = round(random.gauss(20.5, 0.6), 2)
            humidity = round(random.gauss(45, 4), 1)
            particle = int(abs(random.gauss(base_particle * 0.4, base_particle * 0.1)))
            dp = round(random.gauss(12.5, 1.5), 1)   # differential pressure Pa
            # seed an environmental excursion in ROOM-01 for a few hours
            if room_id == "ROOM-01" and 100 <= hour <= 108:
                temp = round(random.gauss(24.5, 0.4), 2)
                particle = int(base_particle * random.uniform(1.2, 1.8))
                dp = round(random.gauss(4.0, 1.0), 1)
            cs.append([ts.isoformat(), room_id, temp, humidity, particle, dp])
    write("cleanroom_sensor_reading.csv",
          ["timestamp", "room_id", "temperature_c", "humidity_pct",
           "particle_count_0_5um", "diff_pressure_pa"], cs)

    # --- Time series: stability study readings for a subset of batches ---
    sr = []
    sample_batches = random.sample(batches, k=12)
    for b in sample_batches:
        batch_id = b[0]
        comp = datetime.fromisoformat(b[5])
        assay0 = random.uniform(99, 101)
        for month in [0, 1, 3, 6, 9, 12]:
            ts = comp + timedelta(days=month * 30)
            # gentle degradation; recalled batches degrade faster
            drop = month * random.uniform(0.3, 0.7)
            if batch_id in bad_batches:
                drop = month * random.uniform(1.2, 2.0)
            assay = round(max(80, assay0 - drop), 2)
            impurity = round(min(5.0, 0.1 + month * random.uniform(0.05, 0.2)), 3)
            sr.append([ts.isoformat(), batch_id, month, assay, impurity,
                       "25C/60RH"])
    write("stability_reading.csv",
          ["timestamp", "batch_id", "month", "assay_percent",
           "impurity_percent", "storage_condition"], sr)

    print("\nSeeded story:")
    print(f"  Bad raw-material lot: {BAD_LOT} (Ketamine HCl, supplier SUP-05 non-GMP)")
    print(f"  Recalled batches: {len(recalled_batches)} -> {recalled_batches[:5]}...")
    affected_rx = [p[0] for p in prescriptions if p[4] in set(recalled_batches)]
    print(f"  Prescriptions dispensed from recalled batches: {len(affected_rx)}")


if __name__ == "__main__":
    main()
