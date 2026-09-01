"""Generate a simple end-to-end DATA FLOW Excalidraw diagram:
how data is generated, flows through Fabric, and is analyzed in the Power BI report."""
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


def label(id, x, y, w, text, font=14, color="#000000"):
    elements.append({
        "type": "text", "id": id, "x": x, "y": y, "width": w,
        "height": int(font * 2.5 * (text.count("\n") + 1)),
        "text": text, "fontSize": font, "fontFamily": 1, "strokeColor": color,
        "textAlign": "left", "verticalAlign": "top",
    })


def arrow(id, x, y, dx, dy, src=None, dst=None, color="#495057", width=2, dashed=False):
    a = {
        "type": "arrow", "id": id, "x": x, "y": y, "width": abs(dx) or 1, "height": abs(dy) or 1,
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
YELLOW_S, YELLOW_F = "#f08c00", "#ffec99"

# ---------------- Title ----------------
label("title", 30, 20, 1500,
      "Constanto Demo - End-to-End Data Flow", 28)
label("subtitle", 30, 64, 1500,
      "How data is generated, flows through Microsoft Fabric, and is analyzed in the Power BI report", 15, "#495057")

# ============ Main spine (generate -> ... -> Power BI -> analyst) ============
SY = 150      # spine y
BW, BH = 190, 108
XS = [30, 255, 480, 705, 930, 1155, 1380]

box("gen", XS[0], SY, BW, BH,
    "1  Generate data\n\ngenerate_data.py\nsynthetic pharma\ncompounding (seed 2026)", BLUE_S, BLUE_F)
box("csv", XS[1], SY, BW, BH,
    "2  17 CSV datasets\n\ndata/*.csv\nentities + time series", BLUE_S, BLUE_F)
box("upload", XS[2], SY, BW, BH,
    "3  Upload to OneLake\n\nupload_to_onelake.py\n-> Files/raw", ORANGE_S, ORANGE_F)
box("lake", XS[3], SY, BW, BH,
    "4  ConstantoLakehouse\n\nPySpark notebook loads\n17 Delta tables (OneLake)", BLUE_S, BLUE_F)
box("sm", XS[4], SY, BW, BH,
    "5  ConstantoOntology\n\nsemantic model\nDirectLake + relationships", GREEN_S, GREEN_F)
box("pbi", XS[5], SY, BW, BH,
    "6  Power BI report\n\nConstanto Recall\nTraceability", TEAL_S, TEAL_F)
box("user", XS[6], SY, BW, BH,
    "7  Analyst / Constanto\n\ninvestigate recall,\nnotify 7 patients", GRAY_S, GRAY_F)

ids = ["gen", "csv", "upload", "lake", "sm", "pbi", "user"]
ay = SY + BH // 2
for i in range(len(ids) - 1):
    rx = XS[i] + BW
    arrow(f"sp{i}", rx, ay, XS[i + 1] - rx, 0, ids[i], ids[i + 1], GRAY_S, 2)

# small stage annotations under the key transform arrows
label("t_load", XS[2] + 150, SY - 24, 150, "PySpark", 11, "#495057")
label("t_dl", XS[3] + 150, SY - 24, 150, "DirectLake", 11, "#2f9e44")
label("t_q", XS[4] + 150, SY - 24, 150, "live query", 11, "#0c8599")

# ============ Real-time branch (below the Lakehouse) ============
RY = 340
box("ehingest", XS[1], RY, BW, 100,
    "Eventhouse ingest\nseed_eventhouse.py\n.ingest from OneLake", ORANGE_S, ORANGE_F)
box("eh", XS[2], RY, BW, 100,
    "ConstantoEventhouse\nKQL time series\n(960 + 72 rows)", YELLOW_S, YELLOW_F)
box("rt", XS[3], RY, BW, 100,
    "Real-time dashboards\n& Data Activator alerts", TEAL_S, TEAL_F)

arrow("rt1", XS[1] + BW, RY + 50, XS[2] - (XS[1] + BW), 0, "ehingest", "eh", ORANGE_S, 2)
arrow("rt2", XS[2] + BW, RY + 50, XS[3] - (XS[2] + BW), 0, "eh", "rt", ORANGE_S, 2)
# Lakehouse/OneLake feeds the real-time ingest (dashed = same OneLake copy)
arrow("rtfeed", XS[3] + 40, SY + BH, -(XS[3] + 40 - (XS[1] + BW // 2)), RY - (SY + BH),
      "lake", "ehingest", ORANGE_S, 2, True)
label("rtlbl", XS[1], RY + 108, 560, "REAL-TIME PATH  -  cleanroom & stability signals", 13, "#e67700")

# ============ Digital Twin Builder (alternative live consumer) ============
box("dtb", XS[4], RY, 405, 100,
    "Digital Twin Builder - ConstantoDigitalTwin\nontology canvas (built LIVE in the demo)\nsame 17 tables, visual entity+relationship graph", PURPLE_S, PURPLE_F, 12)
arrow("dtbfeed", XS[3] + BW, SY + BH - 20, XS[4] + 60 - (XS[3] + BW), RY - (SY + BH - 20),
      "lake", "dtb", PURPLE_S, 2, True)
label("dtblbl", XS[4], RY + 108, 405, "LIVE MODELING PATH  -  the visual demo highlight", 13, "#862e9c")

# ============ Bottom caption ============
box("caption", 30, 500, 1540, 56,
    "DATA FLOW:  generate -> CSV -> OneLake -> Lakehouse (17 Delta tables) -> DirectLake semantic model -> Power BI report.   Real-time signals ingest into the Eventhouse (KQL).   One governed OneLake copy - no data movement between components.",
    GREEN_S, GREEN_F, 13)

diagram = {
    "type": "excalidraw", "version": 2, "source": "copilot",
    "elements": elements, "appState": {"viewBackgroundColor": "#ffffff"},
}
out = r"C:\Workshops\healthcare-ontology-demo\docs\constanto-dataflow-diagram.excalidraw"
with open(out, "w", encoding="utf-8") as f:
    json.dump(diagram, f, indent=2)
print("wrote", out, "with", len(elements), "elements")
