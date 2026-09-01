"""Generate the Constanto ontology + Fabric architecture Excalidraw diagram."""
import json

elements = []


def box(id, x, y, w, h, text, stroke, fill, font=16, dashed=False):
    rect = {
        "type": "rectangle", "id": id, "x": x, "y": y, "width": w, "height": h,
        "strokeColor": stroke, "backgroundColor": fill, "fillStyle": "solid",
        "strokeWidth": 2, "roundness": {"type": 3},
        "boundElements": [{"type": "text", "id": id + "_t"}],
    }
    if dashed:
        rect["strokeStyle"] = "dashed"
    txt = {
        "type": "text", "id": id + "_t", "containerId": id,
        "x": x + 8, "y": y + 8, "width": w - 16, "height": h - 16,
        "text": text, "fontSize": font, "fontFamily": 1, "strokeColor": "#000000",
        "textAlign": "center", "verticalAlign": "middle",
    }
    elements.append(rect)
    elements.append(txt)


def container(id, x, y, w, h, stroke):
    elements.append({
        "type": "rectangle", "id": id, "x": x, "y": y, "width": w, "height": h,
        "strokeColor": stroke, "backgroundColor": "transparent", "fillStyle": "solid",
        "strokeWidth": 2, "strokeStyle": "dotted", "roundness": {"type": 3},
    })


def label(id, x, y, w, text, font=16, color="#000000"):
    elements.append({
        "type": "text", "id": id, "x": x, "y": y, "width": w,
        "height": int(font * 2.5 * (text.count("\n") + 1)),
        "text": text, "fontSize": font, "fontFamily": 1, "strokeColor": color,
        "textAlign": "left", "verticalAlign": "top",
    })


def arrow(id, x, y, dx, dy, src=None, dst=None, color="#495057", width=2, dashed=False):
    a = {
        "type": "arrow", "id": id, "x": x, "y": y, "width": abs(dx), "height": abs(dy),
        "strokeColor": color, "strokeWidth": width, "points": [[0, 0], [dx, dy]],
        "roundness": {"type": 2},
    }
    if dashed:
        a["strokeStyle"] = "dashed"
    if src:
        a["startBinding"] = {"elementId": src, "focus": 0, "gap": 4}
    if dst:
        a["endBinding"] = {"elementId": dst, "focus": 0, "gap": 4}
    elements.append(a)


# Palette
BLUE_S, BLUE_F = "#1864ab", "#a5d8ff"
ORANGE_S, ORANGE_F = "#e67700", "#fff3bf"
PURPLE_S, PURPLE_F = "#862e9c", "#f3d9fa"
GREEN_S, GREEN_F = "#2f9e44", "#b2f2bb"
TEAL_S, TEAL_F = "#0c8599", "#99e9f2"
GRAY_S, GRAY_F = "#495057", "#dee2e6"
RED_S, RED_F = "#D13438", "#FDE7E9"

# ---------------- Title ----------------
label("title", 40, 20, 1400,
      "Constanto Healthcare Ontology on Microsoft Fabric — Digital Twin Builder", 28)
label("subtitle", 40, 64, 1400,
      "From operational data  ->  connected ontology  ->  supplier-to-patient traceability + real-time quality", 16, "#495057")

# ================= LAYER 1: Architecture flow (y ~ 120-250) =================
container("l1box", 30, 110, 1500, 170, GRAY_S)
label("l1lbl", 45, 118, 400, "1)  Fabric data platform (OneLake)", 14, "#495057")

box("src", 55, 160, 210, 90,
    "Operational Systems\nPrescriptions · ERP/BOM\nLIMS · Env. Monitoring", GRAY_S, GRAY_F, 13)
box("lake", 330, 160, 210, 90,
    "OneLake Lakehouse\nConstantoLakehouse\n17 Delta tables", BLUE_S, BLUE_F, 13)
box("eventh", 330, 270, 210, 60,
    "Eventhouse (KQL)\ncleanroom + stability time series", ORANGE_S, ORANGE_F, 12)
box("dtb", 610, 160, 220, 90,
    "Digital Twin Builder\nConstantoDigitalTwin\nONTOLOGY (entities +\nrelationships)", PURPLE_S, PURPLE_F, 13)
box("consume", 900, 160, 230, 90,
    "Consume\nExplore graph · Power BI\nReal-Time Dashboard · Alerts", TEAL_S, TEAL_F, 13)
box("ai", 1190, 160, 210, 90,
    "Extend with AI\nAnomaly detection ·\nAssay prediction", GREEN_S, GREEN_F, 13)

arrow("a1", 265, 205, 60, 0, "src", "lake")
arrow("a2", 540, 205, 65, 0, "lake", "dtb")
arrow("a3", 830, 205, 65, 0, "dtb", "consume")
arrow("a4", 1130, 205, 55, 0, "consume", "ai")
arrow("a5", 435, 270, 0, -20, "eventh", "lake", ORANGE_S, 2, True)

# ================= LAYER 2: Ontology graph (y ~ 330+) =================
container("l2box", 30, 300, 1500, 470, PURPLE_S)
label("l2lbl", 600, 308, 900, "2)  The ontology — connected entities & relationships (with the seeded story)", 14, "#862e9c")

# Forward causal chain
box("supplier", 60, 430, 190, 95,
    "Supplier\nSUP-05\nLowCost Chem Ltd\nGMP certified: NO", RED_S, RED_F, 12)
box("lot", 350, 430, 190, 95,
    "RawMaterialLot\nLOT-0043\nKetamine HCl\nstatus: QUARANTINED", RED_S, RED_F, 12)
box("batch", 640, 430, 190, 95,
    "Batch  (x7)\nstatus: RECALLED\nBATCH-0029, 0050,\n0068, 0072 ...", ORANGE_S, ORANGE_F, 12)
box("rx", 930, 430, 190, 95,
    "Prescription  (x7)\ndispensed from\nrecalled batches", BLUE_S, BLUE_F, 12)
box("patient", 1220, 430, 190, 95,
    "Patient  (x7)\naffected — notify\nNL · ES · US", TEAL_S, TEAL_F, 12)

# Formula above batch, QualityTest below batch
box("formula", 640, 320, 190, 70,
    "Formula\nFORM-03\nKetamine 10% Cream", PURPLE_S, PURPLE_F, 12)
box("qc", 640, 560, 190, 70,
    "QualityTest\nAssay = FAIL\n(83.7% vs 95-105%)", RED_S, RED_F, 12)

# Cleanroom + sensor (real-time)
box("cleanroom", 930, 560, 190, 70,
    "Cleanroom\nROOM-01 (ISO 8)", ORANGE_S, ORANGE_F, 12)
box("sensor", 1220, 560, 190, 70,
    "SensorReading (time series)\ntemp spike + particle\nexcursion ~2025-03-05", ORANGE_S, ORANGE_F, 11)

# Relationship arrows (forward chain)
arrow("r1", 250, 477, 100, 0, "supplier", "lot", GRAY_S, 2)
arrow("r2", 540, 477, 100, 0, "lot", "batch", GRAY_S, 2)
arrow("r3", 830, 477, 100, 0, "batch", "rx", GRAY_S, 2)
arrow("r4", 1120, 477, 100, 0, "rx", "patient", GRAY_S, 2)
arrow("r5", 735, 430, 0, -40, "batch", "formula", PURPLE_S, 2)
arrow("r6", 735, 525, 0, 35, "batch", "qc", RED_S, 2)
arrow("r7", 1025, 525, 0, 35, "batch", "cleanroom", ORANGE_S, 2, True)
arrow("r8", 1120, 595, 100, 0, "cleanroom", "sensor", ORANGE_S, 2)

# Relationship labels
label("rl1", 262, 452, 90, "suppliedBy", 11, "#495057")
label("rl2", 552, 452, 90, "consumedLot", 11, "#495057")
label("rl3", 842, 452, 90, "dispensedAs", 11, "#495057")
label("rl4", 1132, 452, 90, "receivedBy", 11, "#495057")
label("rl5", 745, 395, 110, "producedFrom", 11, "#862e9c")
label("rl6", 745, 530, 90, "testedBy", 11, "#D13438")
label("rl8", 1130, 535, 100, "monitoredBy", 11, "#e67700")

# Trace direction banners
box("backtrace", 60, 660, 480, 44,
    "<-- BACKWARD TRACE:  failed batch  ->  bad lot  ->  non-GMP supplier", RED_S, "#ffffff", 12)
box("fwdtrace", 700, 660, 710, 44,
    "FORWARD TRACE:  recalled batch  ->  prescriptions  ->  exact patients to notify  -->", TEAL_S, "#ffffff", 12)

# Key insight callout
box("insight", 40, 790, 1490, 56,
    "KEY INSIGHT:  1 raw-material lot from a non-GMP supplier  ->  7 recalled batches  ->  7 identifiable patients — traced in SECONDS, not days.  Plus: live cleanroom signals linked to product quality.",
    GREEN_S, GREEN_F, 14)

diagram = {
    "type": "excalidraw", "version": 2, "source": "copilot",
    "elements": elements, "appState": {"viewBackgroundColor": "#ffffff"},
}

out = r"C:\Workshops\healthcare-ontology-demo\docs\constanto-ontology-diagram.excalidraw"
with open(out, "w", encoding="utf-8") as f:
    json.dump(diagram, f, indent=2)
print("wrote", out, "with", len(elements), "elements")
