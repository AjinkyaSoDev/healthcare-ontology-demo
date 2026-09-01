"""Render an Excalidraw diagram to a PNG using Pillow (self-contained, no browser)."""
import json
import math
import sys
from PIL import Image, ImageDraw, ImageFont

SRC = sys.argv[1] if len(sys.argv) > 1 else r"C:\Workshops\healthcare-ontology-demo\docs\constanto-ontology-diagram.excalidraw"
OUT = sys.argv[2] if len(sys.argv) > 2 else SRC.replace(".excalidraw", ".png")

SCALE = 2  # supersample for crisp text
elements = json.load(open(SRC, encoding="utf-8"))["elements"]

# canvas bounds
maxx = max((e["x"] + e.get("width", 0)) for e in elements if e["type"] != "text") + 40
maxy = max((e["y"] + e.get("height", 0)) for e in elements if e["type"] != "text") + 40
W, H = int(maxx), int(maxy)
img = Image.new("RGB", (W * SCALE, H * SCALE), "white")
d = ImageDraw.Draw(img)


def font(sz, bold=False):
    path = r"C:\Windows\Fonts\arialbd.ttf" if bold else r"C:\Windows\Fonts\arial.ttf"
    return ImageFont.truetype(path, int(sz * SCALE))


def S(v):
    return int(v * SCALE)


rects = {e["id"]: e for e in elements if e["type"] == "rectangle"}
texts = {e.get("containerId"): e for e in elements if e["type"] == "text" and e.get("containerId")}

# draw rectangles + bound text
for e in elements:
    if e["type"] == "rectangle":
        x, y, w, h = e["x"], e["y"], e["width"], e["height"]
        fill = e["backgroundColor"]
        if fill == "transparent":
            fill = None
        outline = e["strokeColor"]
        d.rounded_rectangle([S(x), S(y), S(x + w), S(y + h)], radius=S(8),
                            fill=fill, outline=outline, width=max(1, S(1)))
        t = texts.get(e["id"])
        if t:
            lines = t["text"].split("\n")
            fnt = font(t["fontSize"], bold=("title" in e["id"]))
            total_h = len(lines) * t["fontSize"] * 1.35
            cy = y + h / 2 - total_h / 2
            for ln in lines:
                bb = d.textbbox((0, 0), ln, font=fnt)
                lw = bb[2] - bb[0]
                d.text((S(x + w / 2) - lw / 2, S(cy)), ln, fill="#000000", font=fnt)
                cy += t["fontSize"] * 1.35

# draw standalone text
for e in elements:
    if e["type"] == "text" and not e.get("containerId"):
        fnt = font(e["fontSize"], bold=(e["id"] == "title"))
        cyy = e["y"]
        for ln in e["text"].split("\n"):
            d.text((S(e["x"]), S(cyy)), ln, fill=e["strokeColor"], font=fnt)
            cyy += e["fontSize"] * 1.35

# draw arrows
for e in elements:
    if e["type"] == "arrow":
        x, y = e["x"], e["y"]
        pts = e["points"]
        x0, y0 = x + pts[0][0], y + pts[0][1]
        x1, y1 = x + pts[-1][0], y + pts[-1][1]
        col = e["strokeColor"]
        d.line([S(x0), S(y0), S(x1), S(y1)], fill=col, width=max(1, S(1.5)))
        # arrowhead
        ang = math.atan2(y1 - y0, x1 - x0)
        ah = 9
        for da in (math.radians(150), math.radians(-150)):
            hx = x1 + ah * math.cos(ang + da)
            hy = y1 + ah * math.sin(ang + da)
            d.line([S(x1), S(y1), S(hx), S(hy)], fill=col, width=max(1, S(1.5)))

img.save(OUT)
print("wrote", OUT, img.size)
