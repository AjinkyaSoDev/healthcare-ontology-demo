# Demo Script — Constanto Healthcare Ontology on Microsoft Fabric

**Audience:** Constanto (pharmaceutical compounding / personalized medicine).
**Duration:** ~25–30 minutes.
**Big idea:** *"Turn Constanto's disconnected compounding data into one connected digital
twin — so anyone can trace a quality event from supplier to patient in seconds, and see
how the cleanroom environment affects product quality in real time."*

Workspace: `https://app.fabric.microsoft.com/groups/<WORKSPACE_ID>`

**Visual overview:** see `constanto-ontology-diagram.png` (this folder) — keep it open on a
second monitor; it maps every step below.

---

## 0. Set the scene (2 min)

> "Constanto compounds personalized medicines. The data that describes one compounded cream
> — the prescription, the master formula, the raw-material lots and their suppliers, the
> production batch, the lab tests, and the cleanroom it was made in — lives in five or
> six different systems. When something goes wrong, answering *'who is affected?'* means
> a manual, multi-day investigation across all of them.
>
> Today I'll show how Microsoft Fabric's **Digital Twin Builder** turns that into a
> single **ontology** — a connected model of the real things and their relationships —
> so the investigation becomes a few clicks."

---

## 1. The data foundation in Fabric (3 min)

Open **ConstantoLakehouse**. Show the **17 Delta tables**.

Talking points:
* One governed copy in **OneLake** — no data movement, no copies for each tool.
* These tables came from Constanto's operational systems (prescriptions, ERP/BOM, LIMS,
  environmental monitoring). Here they're synthetic but structurally realistic.
* "Individually these are just tables. Watch what happens when we give them *meaning*."

---

## 2. Build the ontology live (8–10 min)

Open **ConstantoDigitalTwin** (Digital Twin Builder). Follow `docs/02-fabric-setup-guide.md`
Part B. Build these live and narrate:

1. **Batch** (map `batch`, ID = batch_id) — "the thing we produce."
2. **Formula** (map `formula`) + relationship **Batch —producedFrom→ Formula**.
3. **RawMaterialLot** (map `raw_material_lot`) + **Batch —consumedLot→ RawMaterialLot**.
4. **Supplier** (map `supplier`) + **RawMaterialLot —suppliedBy→ Supplier**.
5. **QualityTest** (map `quality_test`) + **Batch —testedBy→ QualityTest**.

> "In minutes, with no code, we've modeled the real-world graph: a batch is produced from
> a formula, consumes raw-material lots, those lots come from suppliers, and each batch is
> tested. This is the **ontology**."

Then add the **Cleanroom** entity with the **time-series** signal
(`cleanroom_sensor_reading`) to introduce the Real-Time angle.

---

## 3. The traceability story — the "wow" (6 min)

Use the **Explore** tab (or the SQL fallback in section 5). The seeded scenario:

> **A raw-material lot from a non-GMP supplier caused a batch to fail assay. Who is
> affected?**

Walk it:

1. **Start at the supplier risk.** `Supplier SUP-05` (LowCost Chem Ltd, **GMP certified =
   No**). "Procurement flagged a non-GMP supplier."
2. **Its raw-material lot.** `LOT-0043` — **Ketamine HCl**, status **Quarantined**.
3. **Batches that consumed it.** 7 batches, all **Formula FORM-03 (Ketamine 10% Topical
   Cream)**, now **Recalled**:
   `BATCH-0029, BATCH-0050, BATCH-0068, BATCH-0072, BATCH-0078, BATCH-0084, BATCH-0099`.
4. **The evidence.** Their **QualityTest** rows show **Assay = FAIL** (e.g., BATCH-0072
   assay **83.7%**, spec 95–105%).
5. **Forward to patients.** The prescriptions dispensed from those batches identify the
   exact patients to notify — **7 patients** across NL/ES/US:

   | Prescription | Patient | Batch | Region |
   |---|---|---|---|
   | RX-0013 | PAT-0049 | BATCH-0072 | Barcelona, ES |
   | RX-0070 | PAT-0044 | BATCH-0078 | Wichita, US |
   | RX-0075 | PAT-0022 | BATCH-0029 | Wichita, US |
   | RX-0090 | PAT-0011 | BATCH-0068 | Wichita, US |
   | RX-0107 | PAT-0025 | BATCH-0068 | Amsterdam, NL |
   | RX-0134 | PAT-0056 | BATCH-0072 | Barcelona, ES |
   | RX-0137 | PAT-0058 | BATCH-0084 | Madrid, ES |

> "One bad lot — traced **backward** to a non-GMP supplier and **forward** to the exact
> patients to notify — in seconds, not days. That's the recall and pharmacovigilance
> value of an ontology."

---

## 4. The Real-Time angle — environment vs quality (4 min)

> "Compounding quality depends on the environment it's made in."

* Show the **Cleanroom** entity's time-series signals for **ROOM-01**.
* Around **2025-03-05** there's a seeded **environmental excursion**: temperature spikes
  to ~24.5 °C, **particle count exceeds the ISO 8 limit**, and differential pressure
  drops (a containment risk).
* "Because the twin links live environmental signals to the batches compounded in that
  room, Constanto can flag at-risk product *as conditions drift* — proactive quality, not
  post-hoc investigation."

*(Optional: the same signals are **already ingested live** into **ConstantoEventhouse**
(960 cleanroom readings + 72 stability readings) for KQL / real-time dashboards and
alerting. Open the KQL queryset and run:)*

```kusto
// Environmental excursion in ROOM-01 — particle count over the ISO 8 limit
cleanroom_sensor_reading
| where room_id == "ROOM-01"
| where particle_count_0_5um > 100000 or temperature_c > 23
| order by timestamp asc
```
```kusto
// Stability trend — assay decline over time by batch
stability_reading
| summarize min_assay = min(assay_percent) by batch_id
| where min_assay < 95
| order by min_assay asc
```

---

## 5. SQL fallback queries (reliable backup)

Run these in the **ConstantoLakehouse SQL analytics endpoint** if the canvas is slow live.

**Backward trace — supplier → lot → recalled batches:**
```sql
SELECT b.batch_id, b.formula_id, b.status, l.lot_id, s.name AS supplier, s.gmp_certified
FROM batch b
JOIN batch_raw_material_lot brl ON brl.batch_id = b.batch_id
JOIN raw_material_lot l ON l.lot_id = brl.lot_id
JOIN supplier s ON s.supplier_id = l.supplier_id
WHERE l.lot_id = 'LOT-0043';
```

**The failing evidence:**
```sql
SELECT batch_id, test_type, result, spec_min, spec_max, pass_fail
FROM quality_test
WHERE pass_fail = 'Fail';
```

**Forward trace — affected patients:**
```sql
SELECT rx.prescription_id, p.patient_id, p.display_name, p.region, rx.dispensed_batch_id
FROM prescription rx
JOIN patient p ON p.patient_id = rx.patient_id
JOIN batch b ON b.batch_id = rx.dispensed_batch_id
WHERE b.status = 'Recalled';
```

**Environmental excursion window:**
```sql
SELECT timestamp, room_id, temperature_c, particle_count_0_5um, diff_pressure_pa
FROM cleanroom_sensor_reading
WHERE room_id = 'ROOM-01'
  AND temperature_c > 23
ORDER BY timestamp;
```

---

## 6. Close (2 min)

Tie back to Constanto value:
* **Traceability & recalls** — supplier-to-patient in seconds (GMP / pharmacovigilance).
* **Proactive quality** — environment linked to product in real time.
* **One governed model** — built on OneLake, no data copies, secured by Fabric.
* **Business-user friendly** — the ontology is explorable without SQL.
* **Extensible** — add AI (anomaly detection on sensors, assay prediction), Power BI
  dashboards, and Data Activator alerts on top of the same twin.

**Q&A prompts you may get:** governance/RLS (per-site data boundaries), FHIR/clinical
data integration, real GMP/Annex 1 environmental limits, and how this connects to their
existing LIMS/ERP.
