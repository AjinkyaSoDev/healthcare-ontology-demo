"""Create (or update) a Power BI report (PBIR-Legacy) bound to the ConstantoOntology
semantic model via the Fabric REST API. Tells the recall-traceability story with
cards + tables.

Usage:
  # create a new report
  python src/create_report.py <fabric_token> <workspaceId> <semanticModelId>
  # update an existing report in place
  python src/create_report.py <fabric_token> <workspaceId> <semanticModelId> <reportId>

Why this file looks the way it does
-----------------------------------
Two things are load-bearing and easy to get wrong:

1. `prototypeQuery.Where` is only a cached query *hint*. The Power BI service
   regenerates the visual's query from `projections`, so a predicate that lives
   only in `prototypeQuery` is silently dropped at render time. Real filters must
   go in the visual container's `filters` property.

2. A table visual whose projections are *only* group-by columns gives the engine
   nothing to anchor relationship traversal on, so SUMMARIZECOLUMNS cross-joins
   the tables instead of joining them. Including at least one aggregation makes
   the engine honour the relationships. Without it this report returned
   1,033,340 rows (120 batches x 140 prescriptions x 60 patients) instead of 7.

   The aggregation must sit on the *bridging* table -- the one on the many side of
   both relationships. `batch` and `patient` are both on the one side, joined only
   through `prescription`, so aggregating over `batch` still cross-joins (59,780
   rows). Aggregating over `prescription` collapses it to the correct 7.
"""
import sys, json, uuid, base64, time, requests

TOKEN = sys.argv[1]
WS = sys.argv[2]
MODEL_ID = sys.argv[3]
REPORT_ID = sys.argv[4] if len(sys.argv) > 4 else None
NAME = "Constanto Recall Traceability"

SUM, COUNT_NON_NULL = 0, 5


def gid():
    return "v" + uuid.uuid4().hex[:16]


def col(src, prop, name):
    return {"Column": {"Expression": {"SourceRef": {"Source": src}}, "Property": prop}, "Name": name}


def agg(src, prop, func, name):
    return {"Aggregation": {"Expression": {"Column": {
        "Expression": {"SourceRef": {"Source": src}}, "Property": prop}}, "Function": func}, "Name": name}


def visual_filter(entity, prop, value):
    """A real visual-level filter. This is what actually gets applied at render time."""
    src = entity[0]
    return [{
        "name": uuid.uuid4().hex[:20],
        "expression": {"Column": {"Expression": {"SourceRef": {"Entity": entity}}, "Property": prop}},
        "filter": {
            "Version": 2,
            "From": [{"Name": src, "Entity": entity, "Type": 0}],
            "Where": [{"Condition": {"In": {
                "Expressions": [{"Column": {"Expression": {"SourceRef": {"Source": src}}, "Property": prop}}],
                "Values": [[{"Literal": {"Value": "'" + value + "'"}}]]}}}],
        },
        "type": "Categorical",
        "howCreated": 0,
        "objects": {},
        "isHiddenInViewMode": False,
    }]


def container(x, y, w, h, cfg, filters=None):
    return {"x": float(x), "y": float(y), "z": 0.0, "width": float(w), "height": float(h),
            "config": json.dumps(cfg),
            "filters": json.dumps(filters) if filters else "[]"}


def card_title(text):
    return {"title": [{"properties": {"show": {"expr": {"Literal": {"Value": "true"}}},
                                      "text": {"expr": {"Literal": {"Value": "'" + text + "'"}}}}}]}


RECALLED = visual_filter("batch", "status", "Recalled")
NON_GMP = visual_filter("supplier", "gmp_certified", "No")

# --- Title textbox ---
title_cfg = {
    "name": gid(),
    "layouts": [{"id": 0, "position": {"x": 20, "y": 16, "z": 0, "width": 1240, "height": 56, "tabOrder": 0}}],
    "singleVisual": {
        "visualType": "textbox",
        "drillFilterOtherVisuals": True,
        "objects": {"general": [{"properties": {"paragraphs": [
            {"textRuns": [{"value": "Constanto Pharma - Recall Traceability (supplier -> lot -> batch -> patient)",
                           "textStyle": {"fontSize": "22pt", "fontWeight": "bold", "color": "#0F4C81"}}]}]}}]}
    }
}

# --- Card: recalled batches ---
card_cfg = {
    "name": gid(),
    "layouts": [{"id": 0, "position": {"x": 20, "y": 88, "z": 0, "width": 260, "height": 150, "tabOrder": 1}}],
    "singleVisual": {
        "visualType": "card",
        "projections": {"Values": [{"queryRef": "CountNonNull(batch.batch_id)"}]},
        "prototypeQuery": {
            "Version": 2,
            "From": [{"Name": "b", "Entity": "batch", "Type": 0}],
            "Select": [agg("b", "batch_id", COUNT_NON_NULL, "CountNonNull(batch.batch_id)")],
        },
        "drillFilterOtherVisuals": True,
        "vcObjects": card_title("Recalled batches"),
    }
}

# --- Card: affected patients ---
card2_cfg = {
    "name": gid(),
    "layouts": [{"id": 0, "position": {"x": 300, "y": 88, "z": 0, "width": 260, "height": 150, "tabOrder": 2}}],
    "singleVisual": {
        "visualType": "card",
        "projections": {"Values": [{"queryRef": "CountNonNull(prescription.patient_id)"}]},
        "prototypeQuery": {
            "Version": 2,
            "From": [{"Name": "p", "Entity": "prescription", "Type": 0}],
            "Select": [agg("p", "patient_id", COUNT_NON_NULL, "CountNonNull(prescription.patient_id)")],
        },
        "drillFilterOtherVisuals": True,
        "vcObjects": card_title("Affected patients"),
    }
}

# --- Table: recalled batches -> patients (forward trace) ---
table_cfg = {
    "name": gid(),
    "layouts": [{"id": 0, "position": {"x": 20, "y": 252, "z": 0, "width": 760, "height": 440, "tabOrder": 3}}],
    "singleVisual": {
        "visualType": "tableEx",
        "projections": {"Values": [
            {"queryRef": "batch.batch_id"}, {"queryRef": "batch.formula_id"},
            {"queryRef": "prescription.prescription_id"}, {"queryRef": "patient.patient_id"},
            {"queryRef": "patient.region"},
            {"queryRef": "CountNonNull(prescription.patient_id)"}]},
        "prototypeQuery": {
            "Version": 2,
            "From": [{"Name": "b", "Entity": "batch", "Type": 0},
                     {"Name": "p", "Entity": "prescription", "Type": 0},
                     {"Name": "a", "Entity": "patient", "Type": 0}],
            "Select": [
                col("b", "batch_id", "batch.batch_id"),
                col("b", "formula_id", "batch.formula_id"),
                col("p", "prescription_id", "prescription.prescription_id"),
                col("a", "patient_id", "patient.patient_id"),
                col("a", "region", "patient.region"),
                # Aggregation on the BRIDGE table (prescription) -- see module docstring.
                agg("p", "patient_id", COUNT_NON_NULL, "CountNonNull(prescription.patient_id)")],
        },
        "drillFilterOtherVisuals": True
    }
}

# --- Table: backward trace to the non-GMP supplier / lot ---
supp_cfg = {
    "name": gid(),
    "layouts": [{"id": 0, "position": {"x": 800, "y": 252, "z": 0, "width": 460, "height": 440, "tabOrder": 4}}],
    "singleVisual": {
        "visualType": "tableEx",
        "projections": {"Values": [
            {"queryRef": "raw_material_lot.lot_id"}, {"queryRef": "supplier.name"},
            {"queryRef": "supplier.gmp_certified"}, {"queryRef": "raw_material_lot.qc_status"},
            {"queryRef": "Sum(raw_material_lot.quantity_g)"}]},
        "prototypeQuery": {
            "Version": 2,
            "From": [{"Name": "l", "Entity": "raw_material_lot", "Type": 0},
                     {"Name": "s", "Entity": "supplier", "Type": 0}],
            "Select": [
                col("l", "lot_id", "raw_material_lot.lot_id"),
                col("s", "name", "supplier.name"),
                col("s", "gmp_certified", "supplier.gmp_certified"),
                col("l", "qc_status", "raw_material_lot.qc_status"),
                agg("l", "quantity_g", SUM, "Sum(raw_material_lot.quantity_g)")],
        },
        "drillFilterOtherVisuals": True
    }
}

section = {
    "name": "s" + uuid.uuid4().hex[:16],
    "displayName": "Recall Traceability",
    "filters": "[]",
    "ordinal": 0,
    "visualContainers": [
        container(20, 16, 1240, 56, title_cfg),
        container(20, 88, 260, 150, card_cfg, RECALLED),
        container(300, 88, 260, 150, card2_cfg, RECALLED),
        container(20, 252, 760, 440, table_cfg, RECALLED),
        container(800, 252, 460, 440, supp_cfg, NON_GMP),
    ],
    "config": "{}",
    "displayOption": 1,
    "height": 720.0,
    "width": 1280.0,
}

report_layout = {
    "config": json.dumps({"version": "5.55", "activeSectionIndex": 0,
                          "defaultDrillFilterOtherVisuals": True,
                          "settings": {"useStylableVisualContainerHeader": True}}),
    "layoutOptimization": 0,
    "publicCustomVisuals": [],
    "sections": [section],
}

pbir = {
    "version": "4.0",
    "datasetReference": {
        "byPath": None,
        "byConnection": {
            "connectionString": None,
            "pbiServiceModelId": None,
            "pbiModelVirtualServerName": "sobe_wowvirtualserver",
            "pbiModelDatabaseName": MODEL_ID,
            "name": "EntityDataSource",
            "connectionType": "pbiServiceXmlaStyleLive"
        }
    }
}


def b64(o):
    s = o if isinstance(o, str) else json.dumps(o)
    return base64.b64encode(s.encode("utf-8")).decode("ascii")


parts = [
    {"path": "definition.pbir", "payload": b64(pbir), "payloadType": "InlineBase64"},
    {"path": "report.json", "payload": b64(report_layout), "payloadType": "InlineBase64"},
]

H = {"Authorization": "Bearer " + TOKEN, "Content-Type": "application/json"}
BASE = "https://api.fabric.microsoft.com/v1/workspaces/" + WS + "/reports"

if REPORT_ID:
    url = BASE + "/" + REPORT_ID + "/updateDefinition"
    body = {"definition": {"parts": parts}}
else:
    url = BASE
    body = {"displayName": NAME,
            "description": "Recall traceability from a non-GMP supplier lot to affected patients.",
            "definition": {"parts": parts}}

r = requests.post(url, headers=H, json=body, timeout=120)
print("POST status:", r.status_code)
if r.status_code == 202:
    loc = r.headers.get("Location")
    for _ in range(40):
        time.sleep(5)
        p = requests.get(loc, headers=H, timeout=60)
        st = p.json().get("status")
        print("  status:", st)
        if st in ("Succeeded", "Failed"):
            print(json.dumps(p.json(), indent=2)[:2000])
            break
elif r.status_code in (200, 201):
    print(json.dumps(r.json(), indent=2)[:800] if r.text else "OK")
else:
    print(r.text[:2500])
