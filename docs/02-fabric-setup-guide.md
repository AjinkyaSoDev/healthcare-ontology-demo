# Fabric Setup & Digital Twin Builder Build Guide

Everything below the "Already provisioned" line is **already created in your tenant** by
this demo build. You only need to do the **Digital Twin Builder canvas modeling** live
(Part B) — that is the visual, impressive part of the demo.

---

## Already provisioned (Contoso tenant, F64 capacity)

| Item | Type | ID |
|---|---|---|
| **Constanto-Healthcare-Ontology-Demo** | Workspace | `<WORKSPACE_ID>` |
| **ConstantoLakehouse** | Lakehouse (17 Delta tables) | `<LAKEHOUSE_ID>` |
| **ConstantoEventhouse** | Eventhouse (KQL) — **seeded**: 960 cleanroom + 72 stability rows | `<EVENTHOUSE_ID>` |
| **Load_Constanto_Tables** | Notebook (reproducible loader) | `<NOTEBOOK_ID>` |
| **ConstantoDigitalTwin** | Digital Twin Builder (ontology canvas) | `<DIGITAL_TWIN_ID>` |
| **ConstantoOntology** | Semantic model — 15 entities + relationships (**built, queryable**) | `<SEMANTIC_MODEL_ID>` |

Open the workspace:
`https://app.fabric.microsoft.com/groups/<WORKSPACE_ID>`

The 17 Delta tables are the **ontology source**:
`site, cleanroom, equipment, supplier, ingredient, formula, formula_ingredient,
operator, prescriber, patient, raw_material_lot, batch, batch_raw_material_lot,
prescription, quality_test, cleanroom_sensor_reading, stability_reading`.

---

## Part A — (Optional) Rebuild from scratch

If you ever need to recreate the data foundation:

```powershell
cd C:\Workshops\healthcare-ontology-demo
python src\generate_data.py                       # -> data\*.csv

# get tokens
$stg = az account get-access-token --resource "https://storage.azure.com" --query accessToken -o tsv
$fab = az account get-access-token --resource "https://api.fabric.microsoft.com" --query accessToken -o tsv

# upload + load (uses the existing workspace/lakehouse IDs above)
python src\upload_to_onelake.py $stg <WORKSPACE_ID> <LAKEHOUSE_ID>
python src\create_and_run_notebook.py $fab <WORKSPACE_ID> <LAKEHOUSE_ID> ConstantoLakehouse
```

---

## Part B — Build the ontology in Digital Twin Builder (live, ~10 min)

Open **ConstantoDigitalTwin** in the workspace. You land on the **semantic canvas**.

> Preview note: Digital Twin Builder is in preview and the canvas is UI-driven. Build a
> focused subset live (5 entities) to tell the traceability story; the rest can be
> described. Steps follow the DTB flow: **add entity type → map data → add properties →
> define relationships → explore.**

### B1. Add the core entity types (map from Lakehouse tables)

For each entity below: **+ Add entity type** → **Map data** → pick **ConstantoLakehouse** →
select the table → set the **unique ID** property → add the listed properties.

| Entity type | Table | Unique ID | Properties to include |
|---|---|---|---|
| **Batch** | `batch` | batch_id | formula_id, site_id, compounded_date, status, quantity_units |
| **Formula** | `formula` | formula_id | name, dosage_form, route, therapeutic_area |
| **RawMaterialLot** | `raw_material_lot` | lot_id | ingredient_id, supplier_id, qc_status, expiry_date |
| **Supplier** | `supplier` | supplier_id | name, country, gmp_certified |
| **QualityTest** | `quality_test` | test_id | batch_id, test_type, result, pass_fail |

*(If time allows, also add `Patient`, `Prescription`, `Ingredient`, `Cleanroom`.)*

### B2. Add the time-series entity (the Real-Time angle)

1. **+ Add entity type** → name it **Cleanroom** → map `cleanroom` table → unique ID
   `room_id` → add non-time-series property `iso_class`. *(DTB requires at least one
   non-time-series property before adding time series.)*
2. On **Cleanroom**, **Map data → time series** → pick `cleanroom_sensor_reading` →
   join key **room_id** → map signals `temperature_c`, `particle_count_0_5um`,
   `diff_pressure_pa`, timestamp = `timestamp`.

### B3. Define relationships

Use **+ Add relationship** and map each to the join column:

| From | Relationship | To | Join |
|---|---|---|---|
| Batch | producedFrom | Formula | batch.formula_id = formula.formula_id |
| Batch | consumedLot | RawMaterialLot | via `batch_raw_material_lot` (batch_id, lot_id) |
| Batch | testedBy | QualityTest | quality_test.batch_id = batch.batch_id |
| RawMaterialLot | suppliedBy | Supplier | raw_material_lot.supplier_id = supplier.supplier_id |
| Batch | compoundedAt | Pharmacy(Site) *(if added)* | batch.site_id = site.site_id |

> `batch_raw_material_lot` is a **many-to-many link table** — model `consumedLot` as a
> relationship that resolves through it, not as its own entity.

### B4. Explore

Open the **Explore** tab. Select entity **RawMaterialLot** → instance **LOT-0043** →
walk its relationships to see the consuming batches, their failed quality tests, and
(if modeled) the affected prescriptions/patients. This is the money shot.

---

## Part C — Backup: prove the story in SQL (if the canvas is slow live)

The Lakehouse **SQL analytics endpoint** answers the same questions. Use these in the
SQL endpoint query editor as a reliable fallback — see `docs/03-demo-script.md` for the
exact queries and expected results.

---

## Part D — Power BI semantic model (ALREADY BUILT: `ConstantoOntology`)

A DirectLake semantic model is **already provisioned** over the same 17 tables — this is
the ontology as a connected, queryable model (no data copy, no refresh):

* **ConstantoOntology** — id `<SEMANTIC_MODEL_ID>`
* **15 entity tables** with the full **relationship graph** (supplier→lot→batch→
  prescription→patient, plus formula, quality_test, cleanroom, site/operator/equipment).
* Built via `src\create_semantic_model.py` (TMDL / Fabric REST API).

**Verify / demo it (DAX via the semantic model):**
```dax
EVALUATE
ROW(
  "recalled_batches", COUNTROWS(FILTER('batch', 'batch'[status]="Recalled")),
  "affected_patients", CALCULATE(DISTINCTCOUNT('prescription'[patient_id]),
                                 FILTER('batch', 'batch'[status]="Recalled"))
)
```
Returns **recalled_batches = 7, affected_patients = 7** — the traceability story resolved
purely through the ontology relationships.

To build a report: open **ConstantoOntology** in the workspace → **Create report** → drag a
table of `batch[batch_id]`, `prescription[patient_id]`, `patient[region]` and filter
`batch[status] = "Recalled"`.

### Power BI report ALREADY BUILT: `Constanto Recall Traceability`

A ready-to-present report is provisioned over the model — id
`<REPORT_ID>`. Page **"Recall Traceability"** contains:
* Card **Recalled batches = 7**; Card **Affected patients = 7**.
* Table: the exact 7 affected patients (batch → prescription → patient → region).
* Table: the non-GMP supplier's lots (LowCost Chem Ltd, `gmp_certified = No`), incl.
  quarantined `LOT-0043`.
* Built + verified via `src\create_report.py` (PBIR-Legacy, Fabric REST API). It filters
  `batch[status] = "Recalled"` at the visual level.

> **Two pitfalls when authoring PBIR-Legacy visuals via the REST API** (both were live
> bugs in an earlier version of this report — it loaded ~1M rows and showed the wrong
> numbers):
>
> 1. **Put filters in the visual container's `filters` property, not just
>    `prototypeQuery.Where`.** `prototypeQuery` is a cached query *hint*; the service
>    regenerates the visual's query from `projections` at render time and silently drops
>    a predicate that only lives there.
> 2. **Every table visual needs at least one aggregation, on the *bridging* table.**
>    With group-by columns only, `SUMMARIZECOLUMNS` cross-joins instead of joining.
>    Here `batch` and `patient` are both on the *one* side and are connected only through
>    `prescription`, so the aggregation must be over `prescription`. Measured on this
>    model: no aggregation → **1,033,340 rows**; aggregation on `batch` → **59,780 rows**;
>    aggregation on `prescription` → **7 rows**.

> Note on relationships: 5 edges are set **inactive** (operator→site, equipment→site,
> batch_raw_material_lot→ingredient, prescription→formula, formula_ingredient→ingredient)
> to keep a single unambiguous active filter path. They still document the ontology and
> are usable in DAX via `USERELATIONSHIP`.

### (Optional) Rebuild the semantic model
```powershell
cd C:\Workshops\healthcare-ontology-demo
$stg = az account get-access-token --resource "https://storage.azure.com" --query accessToken -o tsv
python src\fetch_schemas.py $stg                  # -> fabric\schemas.json
$fab = az account get-access-token --resource "https://api.fabric.microsoft.com" --query accessToken -o tsv
python src\create_semantic_model.py $fab
```
