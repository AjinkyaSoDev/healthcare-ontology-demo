"""Create a Power BI report (PBIR-Legacy) bound to the ConstantoOntology semantic model,
via the Fabric REST API. Tells the recall-traceability story with a card + tables."""
import sys, json, uuid, base64, time, requests

TOKEN = sys.argv[1]
WS = "<WORKSPACE_ID>"
MODEL_ID = "<SEMANTIC_MODEL_ID>"
NAME = "Constanto Recall Traceability"


def gid():
    return "v" + uuid.uuid4().hex[:16]


def col(src, entity, prop, name):
    return {"Column": {"Expression": {"SourceRef": {"Source": src}}, "Property": prop}, "Name": name}


def where_recalled(src):
    return [{"Condition": {"Comparison": {"ComparisonKind": 0,
            "Left": {"Column": {"Expression": {"SourceRef": {"Source": src}}, "Property": "status"}},
            "Right": {"Literal": {"Value": "'Recalled'"}}}}}]


def container(x, y, w, h, cfg):
    return {"x": float(x), "y": float(y), "z": 0.0, "width": float(w), "height": float(h),
            "config": json.dumps(cfg), "filters": "[]"}


# --- Title textbox ---
title_cfg = {
    "name": gid(),
    "layouts": [{"id": 0, "position": {"x": 20, "y": 16, "z": 0, "width": 1240, "height": 56, "tabOrder": 0}}],
    "singleVisual": {
        "visualType": "textbox",
        "drillFilterOtherVisuals": True,
        "objects": {"general": [{"properties": {"paragraphs": [
            {"textRuns": [{"value": "Constanto - Recall Traceability (supplier -> lot -> batch -> patient)",
                           "textStyle": {"fontSize": "22pt", "fontWeight": "bold", "color": "#0F4C81"}}]}]}}]}
    }
}

# --- Card: recalled batches count ---
card_cfg = {
    "name": gid(),
    "layouts": [{"id": 0, "position": {"x": 20, "y": 88, "z": 0, "width": 260, "height": 150, "tabOrder": 1}}],
    "singleVisual": {
        "visualType": "card",
        "projections": {"Values": [{"queryRef": "CountNonNull(batch.batch_id)"}]},
        "prototypeQuery": {
            "Version": 2,
            "From": [{"Name": "b", "Entity": "batch", "Type": 0}],
            "Select": [{"Aggregation": {"Expression": {"Column": {"Expression": {"SourceRef": {"Source": "b"}},
                        "Property": "batch_id"}}, "Function": 5}, "Name": "CountNonNull(batch.batch_id)"}],
            "Where": where_recalled("b")
        },
        "drillFilterOtherVisuals": True,
        "vcObjects": {"title": [{"properties": {"show": {"expr": {"Literal": {"Value": "true"}}},
                     "text": {"expr": {"Literal": {"Value": "'Recalled batches'"}}}}}]}
    }
}

# --- Card: distinct affected patients (count on the filtered prescription side) ---
card2_cfg = {
    "name": gid(),
    "layouts": [{"id": 0, "position": {"x": 300, "y": 88, "z": 0, "width": 260, "height": 150, "tabOrder": 2}}],
    "singleVisual": {
        "visualType": "card",
        "projections": {"Values": [{"queryRef": "CountNonNull(prescription.patient_id)"}]},
        "prototypeQuery": {
            "Version": 2,
            "From": [{"Name": "b", "Entity": "batch", "Type": 0},
                     {"Name": "p", "Entity": "prescription", "Type": 0}],
            "Select": [{"Aggregation": {"Expression": {"Column": {"Expression": {"SourceRef": {"Source": "p"}},
                        "Property": "patient_id"}}, "Function": 5}, "Name": "CountNonNull(prescription.patient_id)"}],
            "Where": where_recalled("b")
        },
        "drillFilterOtherVisuals": True,
        "vcObjects": {"title": [{"properties": {"show": {"expr": {"Literal": {"Value": "true"}}},
                     "text": {"expr": {"Literal": {"Value": "'Affected patients'"}}}}}]}
    }
}

# --- Table: recalled batches -> patients ---
table_cfg = {
    "name": gid(),
    "layouts": [{"id": 0, "position": {"x": 20, "y": 252, "z": 0, "width": 760, "height": 440, "tabOrder": 3}}],
    "singleVisual": {
        "visualType": "tableEx",
        "projections": {"Values": [
            {"queryRef": "batch.batch_id"}, {"queryRef": "batch.formula_id"},
            {"queryRef": "prescription.prescription_id"}, {"queryRef": "patient.patient_id"},
            {"queryRef": "patient.region"}]},
        "prototypeQuery": {
            "Version": 2,
            "From": [{"Name": "b", "Entity": "batch", "Type": 0},
                     {"Name": "p", "Entity": "prescription", "Type": 0},
                     {"Name": "a", "Entity": "patient", "Type": 0}],
            "Select": [
                col("b", "batch", "batch_id", "batch.batch_id"),
                col("b", "batch", "formula_id", "batch.formula_id"),
                col("p", "prescription", "prescription_id", "prescription.prescription_id"),
                col("a", "patient", "patient_id", "patient.patient_id"),
                col("a", "patient", "region", "patient.region")],
            "Where": where_recalled("b")
        },
        "drillFilterOtherVisuals": True
    }
}

# --- Table: backward trace supplier/lot for the recalled batches ---
supp_cfg = {
    "name": gid(),
    "layouts": [{"id": 0, "position": {"x": 800, "y": 252, "z": 0, "width": 460, "height": 440, "tabOrder": 4}}],
    "singleVisual": {
        "visualType": "tableEx",
        "projections": {"Values": [
            {"queryRef": "raw_material_lot.lot_id"}, {"queryRef": "supplier.name"},
            {"queryRef": "supplier.gmp_certified"}, {"queryRef": "raw_material_lot.qc_status"}]},
        "prototypeQuery": {
            "Version": 2,
            "From": [{"Name": "l", "Entity": "raw_material_lot", "Type": 0},
                     {"Name": "s", "Entity": "supplier", "Type": 0}],
            "Select": [
                col("l", "raw_material_lot", "lot_id", "raw_material_lot.lot_id"),
                col("s", "supplier", "name", "supplier.name"),
                col("s", "supplier", "gmp_certified", "supplier.gmp_certified"),
                col("l", "raw_material_lot", "qc_status", "raw_material_lot.qc_status")],
            "Where": [{"Condition": {"Comparison": {"ComparisonKind": 0,
                      "Left": {"Column": {"Expression": {"SourceRef": {"Source": "s"}}, "Property": "gmp_certified"}},
                      "Right": {"Literal": {"Value": "'No'"}}}}}]
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
        container(20, 88, 260, 150, card_cfg),
        container(300, 88, 260, 150, card2_cfg),
        container(20, 252, 760, 440, table_cfg),
        container(800, 252, 460, 440, supp_cfg),
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

body = {"displayName": NAME,
        "description": "Power BI report over ConstantoOntology: recall traceability from non-GMP supplier lot to affected patients.",
        "definition": {"parts": parts}}

H = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}
r = requests.post(f"https://api.fabric.microsoft.com/v1/workspaces/{WS}/reports", headers=H, json=body, timeout=120)
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
    print(json.dumps(r.json(), indent=2)[:800])
else:
    print(r.text[:2500])
