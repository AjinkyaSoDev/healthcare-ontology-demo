# Constanto Compounding Ontology — Design

This is the semantic model (ontology) you build in **Microsoft Fabric Digital Twin
Builder (DTB)** for the demo. It represents Constanto's pharmaceutical compounding
operation: from a physician's prescription, through the compounded formula and its
ingredients, to the production batch, quality testing, and the cleanroom environment —
all connected so you can traverse the graph in any direction.

## Why an ontology (not just tables)

Constanto's data lives in many systems: prescriptions, ERP/BOM, lab (LIMS), environmental
monitoring, supplier records. Individually they answer narrow questions. An **ontology**
turns them into one connected model of *real-world things and their relationships*, so a
business user can ask: *"This batch failed assay — which raw-material lot and supplier
caused it, and which patients received it?"* and traverse the answer as a graph.

## Entity types (16)

| Entity type | Source table | Key | Notable properties |
|---|---|---|---|
| **Patient** | `patient` | patient_id | birth_year, weight_kg, allergies, region |
| **Prescriber** | `prescriber` | prescriber_id | specialty, clinic |
| **Prescription** | `prescription` | prescription_id | frequency, status, prescription_date |
| **Formula** | `formula` | formula_id | dosage_form, route, therapeutic_area |
| **Ingredient** | `ingredient` | ingredient_id | type (API/Excipient), cas_number, hazard_class |
| **RawMaterialLot** | `raw_material_lot` | lot_id | received/expiry date, qc_status, quantity |
| **Supplier** | `supplier` | supplier_id | country, gmp_certified |
| **Batch** | `batch` | batch_id | compounded_date, expiry_date, quantity, status |
| **QualityTest** | `quality_test` | test_id | test_type, result, spec_min/max, pass_fail |
| **Pharmacy (Site)** | `site` | site_id | location, license |
| **Cleanroom** | `cleanroom` | room_id | iso_class |
| **Equipment** | `equipment` | equipment_id | type |
| **Operator** | `operator` | operator_id | role |
| **CleanroomSensorReading** *(time series)* | `cleanroom_sensor_reading` | room_id + timestamp | temperature_c, humidity_pct, particle_count, diff_pressure_pa |
| **StabilityReading** *(time series)* | `stability_reading` | batch_id + timestamp | assay_percent, impurity_percent |
| **FormulaIngredient** *(link/BOM)* | `formula_ingredient` | formula_id + ingredient_id | quantity, unit, function |

> **Time-series entities** are what make this a *Real-Time Intelligence* ontology.
> In DTB you add at least one non-time-series property to an entity, then map the
> time-series signal and join on the key (e.g., `room_id`).

## Relationship types

```
Patient        --hasPrescription-->  Prescription
Prescriber     --wrote----------->   Prescription
Prescription   --forFormula------>   Formula
Prescription   --dispensedAs----->   Batch          (dispensed_batch_id)
Formula        --contains-------->   Ingredient     (via FormulaIngredient BOM)
Batch          --producedFrom---->   Formula
Batch          --compoundedAt---->   Pharmacy(Site)
Batch          --compoundedBy---->   Operator
Batch          --usedEquipment-->    Equipment
Batch          --consumedLot----->   RawMaterialLot (via batch_raw_material_lot)
Batch          --testedBy-------->   QualityTest
Batch          --hasStability---->   StabilityReading
RawMaterialLot --isOf------------>   Ingredient
RawMaterialLot --suppliedBy------>   Supplier
Pharmacy(Site) --hasCleanroom---->   Cleanroom
Cleanroom      --monitoredBy----->   CleanroomSensorReading
```

## The traceability graph (the "wow" moment)

```
   Supplier(SUP-05, non-GMP)
        |  suppliedBy
        v
   RawMaterialLot(LOT-0043, Ketamine HCl, QUARANTINED)
        |  consumedLot
        v
   Batch(status=Recalled) --testedBy--> QualityTest(Assay = FAIL, 80-89%)
        |  dispensedAs (reverse)
        v
   Prescription --hasPrescription(reverse)--> Patient   <-- who to notify
```

One bad lot, traced **backward** to a non-GMP supplier and **forward** to the exact
patients affected — in a few graph hops. That is the value of the ontology.

## Environmental correlation (Real-Time angle)

`Cleanroom ROOM-01` has a **seeded environmental excursion** (temperature spike to
~24.5 C, particle count above ISO 8 limit, differential pressure drop) around
2025-03-05. In the demo you correlate that time window with batches compounded in that
room — showing how the digital twin links **live environmental signals** to product
quality risk.

## Design notes for the demo

* **Grain matters.** Dimension entities (Patient, Formula, Supplier...) are 1 row = 1
  instance. Link tables (`formula_ingredient`, `batch_raw_material_lot`) become
  *relationships*, not entities — model them as relationship mappings in DTB.
* **Keys are the glue.** Every relationship is a foreign-key join; keep the ID columns
  clean (they already are in the generated data).
* **Start small on stage.** Build 4–5 entity types live (Batch, Formula, Ingredient,
  RawMaterialLot, Supplier) and show traceability; mention the rest are pre-modeled.
