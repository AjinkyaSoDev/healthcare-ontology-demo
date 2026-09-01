"""Generate a MEDALLION-architecture (Bronze/Silver/Gold) data-flow Excalidraw diagram
for the Constanto Fabric demo."""
import json

elements = []


def box(id, x, y, w, h, text, stroke, fill, font=13):
    elements.append({
        "type": "rectangle", "id": id, "x": x, "y": y, "width": w, "height": h,
        "strokeColor": stroke, "backgroundColor": fill, "fillStyle": "solid",
        "strokeWidth": 2, "roundness": {"type": 3},
        "boundElements": [{"type": "text", "id": id + "_t"}],
    })
    elements.append({
        "type": "text", "id": id + "_t", "containerId": id,
        "x": x + 8, "y": y + 8, "width": w - 16, "height": h - 16,
        "text": text, "fontSize": font, "fontFamily": 1, "strokeColor": "#000000",
        "textAlign": "center", "verticalAlign": "middle",
    })


def container(id, x, y, w, h, stroke):
    elements.append({
        "type": "rectangle", "id": id, "x": x, "y": y, "width": w, "height": h,
        "strokeColor": stroke, "backgroundColor": "transparent", "fillStyle": "solid",
        "strokeWidth": 2, "strokeStyle": "dotted", "roundness": {"type": 3},
    })


def label(id, x, y, w, text, font=14, color="#000000"):
    elements.append({
        "type": "text", "id": id, "x": x, "y": y, "width": w,
        "height": int(font * 2.5 * (text.count("\n") + 1)),
        "text": text, "fontSize": font, "fontFamily": 1, "strokeColor": color,
        "textAlign": "left", "verticalAlign": "top",
    })


def arrow(id, x, y, dx, dy, color="#495057", width=2, dashed=False):
    a = {
        "type": "arrow", "id": id, "x": x, "y": y, "width": abs(dx) or 1, "height": abs(dy) or 1,
        "strokeColor": color, "strokeWidth": width, "points": [[0, 0], [dx, dy]],
        "roundness": {"type": 2},
    }
    if dashed:
        a["strokeStyle"] = "dashed"
    elements.append(a)


# Palette
GRAY_S, GRAY_F = "#495057", "#dee2e6"
BRONZE_S, BRONZE_F = "#A15C07", "#F3C89B"
SILVER_S, SILVER_F = "#5B6B7B", "#DDE3EA"
GOLD_S, GOLD_F = "#B7791F", "#FCE9A6"
TEAL_S, TEAL_F = "#0c8599", "#99e9f2"
GREEN_S, GREEN_F = "#2f9e44", "#b2f2bb"
PURPLE_S, PURPLE_F = "#862e9c", "#f3d9fa"

# ---------------- Title ----------------
label("title", 30, 20, 1600, "Constanto Demo - Medallion Architecture on Microsoft Fabric", 28)
label("subtitle", 30, 64, 1600,
      "Bronze (raw)  ->  Silver (cleansed & conformed)  ->  Gold (curated business model)  ->  served to the Power BI report", 15, "#495057")

# ---------------- Band containers + headers ----------------
BY, BH = 120, 620
bands = [
    ("bSrc", 30, 250, GRAY_S, "SOURCE", "data generation"),
    ("bBron", 300, 270, BRONZE_S, "BRONZE", "raw landing (as-is)"),
    ("bSil", 590, 300, SILVER_S, "SILVER", "cleansed & conformed"),
    ("bGold", 910, 300, GOLD_S, "GOLD", "curated business model"),
    ("bCons", 1230, 440, TEAL_S, "CONSUMPTION", "serve & analyze"),
]
for bid, bx, bw, col, name, desc in bands:
    container(bid, bx, BY, bw, BH, col)
    label(bid + "_h", bx + 14, BY + 12, bw - 20, name, 18, col)
    label(bid + "_d", bx + 14, BY + 42, bw - 20, desc, 12, "#495057")

# ---------------- Boxes ----------------
# Source
box("gen", 45, 190, 220, 120,
    "generate_data.py\n\nsynthetic pharma\ncompounding data (seed 2026)", GRAY_S, GRAY_F, 12)
box("csv", 45, 350, 220, 110,
    "17 CSV datasets\ndata/*.csv\nentities + time series", GRAY_S, GRAY_F, 12)
# Bronze
box("raw", 320, 300, 230, 180,
    "OneLake  Files/raw\n\nupload_to_onelake.py\nraw CSV landing\n(immutable, unmodified)", BRONZE_S, BRONZE_F, 12)
# Silver
box("delta", 610, 190, 270, 150,
    "17 Delta tables\n\nPySpark: Load_Constanto_Tables\ntyped - conformed - deduped\n(ConstantoLakehouse)", SILVER_S, SILVER_F, 12)
box("eh", 610, 600, 270, 120,
    "ConstantoEventhouse (KQL)\ncleanroom + stability\ntime series (960 + 72 rows)", SILVER_S, SILVER_F, 12)
# Gold
box("sm", 930, 190, 270, 150,
    "ConstantoOntology\n\nDirectLake semantic model\nbusiness entities + relationships", GOLD_S, GOLD_F, 12)
box("dtb", 930, 400, 270, 150,
    "Digital Twin Builder\nConstantoDigitalTwin\nontology canvas (built LIVE)\nvisual entity+relationship graph", PURPLE_S, PURPLE_F, 11)
# Consumption
box("pbi", 1250, 190, 400, 130,
    "Power BI report\nConstanto Recall Traceability\n(recalled batches -> patients)", TEAL_S, TEAL_F, 13)
box("analyst", 1250, 400, 400, 130,
    "Analyst / Constanto\ninvestigate recall,\nnotify 7 identified patients", GREEN_S, GREEN_F, 13)
box("rt", 1250, 600, 400, 120,
    "Real-time dashboards\n& Data Activator alerts", TEAL_S, TEAL_F, 13)

# ---------------- Arrows ----------------
arrow("f_gc", 155, 310, 0, 40, GRAY_S)                       # gen -> csv
arrow("f_cr", 265, 405, 55, -15, GRAY_S)                     # csv -> raw
arrow("f_rd", 550, 360, 60, -70, BRONZE_S)                   # raw -> delta (cleanse)
arrow("f_re", 550, 430, 60, 200, BRONZE_S, 2, True)          # raw -> eh (ingest TS)
arrow("f_ds", 880, 265, 50, 0, SILVER_S)                     # delta -> sm (DirectLake)
arrow("f_dd", 880, 300, 50, 175, SILVER_S, 2, True)          # delta -> dtb (map live)
arrow("f_sp", 1200, 260, 50, -5, GOLD_S)                     # sm -> pbi (live query)
arrow("f_pa", 1450, 320, 0, 80, TEAL_S)                      # pbi -> analyst
arrow("f_da", 1200, 470, 50, -5, PURPLE_S, 2, True)          # dtb -> analyst (explore)
arrow("f_er", 880, 660, 370, 0, SILVER_S)                    # eh -> rt (real-time)

# arrow labels
label("l_rd", 545, 300, 130, "cleanse /\nconform", 11, "#A15C07")
label("l_re", 555, 520, 130, "ingest\ntime series", 11, "#A15C07")
label("l_ds", 885, 232, 120, "DirectLake", 11, "#5B6B7B")
label("l_sp", 1200, 228, 120, "live query", 11, "#B7791F")
label("l_er", 980, 632, 160, "real-time streaming", 11, "#5B6B7B")

# ---------------- Bottom caption ----------------
box("caption", 30, 770, 1620, 56,
    "MEDALLION:  Bronze = raw CSVs landed in OneLake (unmodified)   |   Silver = cleansed, typed, conformed Delta tables   |   Gold = curated ConstantoOntology semantic model (business entities + relationships)   ->   served to Power BI.  One OneLake copy, no data movement.",
    GREEN_S, GREEN_F, 12)

diagram = {
    "type": "excalidraw", "version": 2, "source": "copilot",
    "elements": elements, "appState": {"viewBackgroundColor": "#ffffff"},
}
out = r"C:\Workshops\healthcare-ontology-demo\docs\constanto-medallion-diagram.excalidraw"
with open(out, "w", encoding="utf-8") as f:
    json.dump(diagram, f, indent=2)
print("wrote", out, "with", len(elements), "elements")
