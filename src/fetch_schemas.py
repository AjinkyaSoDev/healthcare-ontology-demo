"""Fetch Delta table schemas from the OneLake _delta_log and save as JSON."""
import sys, json, requests

token = sys.argv[1]
WS = "<WORKSPACE_ID>"
LH = "<LAKEHOUSE_ID>"
H = {"Authorization": f"Bearer {token}"}

TABLES = ["supplier","raw_material_lot","batch_raw_material_lot","batch","formula",
          "quality_test","prescription","patient","cleanroom","ingredient",
          "formula_ingredient","prescriber","site","operator","equipment"]

# Spark type -> TMDL dataType
def map_type(t):
    if isinstance(t, dict):
        return "string"  # nested -> treat as string (shouldn't happen here)
    t = t.lower()
    if t in ("string","binary"): return "string"
    if t in ("boolean",): return "boolean"
    if t in ("byte","short","integer","long"): return "int64"
    if t in ("float","double"): return "double"
    if t.startswith("decimal"): return "decimal"
    if t in ("date","timestamp","timestamp_ntz"): return "dateTime"
    return "string"

schemas = {}
for t in TABLES:
    url = f"https://onelake.dfs.fabric.microsoft.com/{WS}/{LH}/Tables/{t}/_delta_log/00000000000000000000.json"
    r = requests.get(url, headers=H, timeout=60)
    r.raise_for_status()
    meta = None
    for line in r.text.splitlines():
        line = line.strip()
        if not line:
            continue
        obj = json.loads(line)
        if "metaData" in obj:
            meta = obj["metaData"]
            break
    schema = json.loads(meta["schemaString"])
    cols = [(f["name"], map_type(f["type"])) for f in schema["fields"]]
    schemas[t] = cols
    print(f"{t}: " + ", ".join(f"{n}:{ty}" for n, ty in cols))

json.dump(schemas, open(r"C:\Workshops\healthcare-ontology-demo\fabric\schemas.json","w"), indent=2)
print("\nsaved fabric/schemas.json")
