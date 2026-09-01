"""Generate a DirectLake semantic-model (TMDL) over ConstantoLakehouse and create it
via the Fabric REST API. This is the 'ontology' as a connected, queryable model:
15 entity tables + the relationship graph."""
import sys, json, uuid, base64, time, requests

TOKEN = sys.argv[1]
WS = "<WORKSPACE_ID>"
SQL_SERVER = "<SQL_ENDPOINT_HOST>"
SQL_DB = "<SQL_ENDPOINT_ID>"  # SQL endpoint id (database name)
NAME = "ConstantoOntology"

schemas = json.load(open(r"C:\Workshops\healthcare-ontology-demo\fabric\schemas.json"))

# ontology edges: (from_table, from_col, to_table, to_col)
RELS = [
    ("raw_material_lot", "supplier_id", "supplier", "supplier_id"),
    ("raw_material_lot", "ingredient_id", "ingredient", "ingredient_id"),
    ("batch_raw_material_lot", "batch_id", "batch", "batch_id"),
    ("batch_raw_material_lot", "lot_id", "raw_material_lot", "lot_id"),
    ("batch_raw_material_lot", "ingredient_id", "ingredient", "ingredient_id"),
    ("batch", "formula_id", "formula", "formula_id"),
    ("batch", "site_id", "site", "site_id"),
    ("batch", "operator_id", "operator", "operator_id"),
    ("batch", "equipment_id", "equipment", "equipment_id"),
    ("quality_test", "batch_id", "batch", "batch_id"),
    ("prescription", "patient_id", "patient", "patient_id"),
    ("prescription", "prescriber_id", "prescriber", "prescriber_id"),
    ("prescription", "formula_id", "formula", "formula_id"),
    ("prescription", "dispensed_batch_id", "batch", "batch_id"),
    ("formula_ingredient", "formula_id", "formula", "formula_id"),
    ("formula_ingredient", "ingredient_id", "ingredient", "ingredient_id"),
    ("cleanroom", "site_id", "site", "site_id"),
    ("operator", "site_id", "site", "site_id"),
    ("equipment", "site_id", "site", "site_id"),
]

TABLES = list(schemas.keys())

# edges that must be INACTIVE to keep a single active path between any two tables
INACTIVE = {
    ("batch_raw_material_lot", "ingredient_id"),  # reach ingredient via raw_material_lot
    ("operator", "site_id"),                        # reach site via batch
    ("equipment", "site_id"),                       # reach site via batch
    ("prescription", "formula_id"),                 # reach formula via dispensed batch
    ("formula_ingredient", "ingredient_id"),        # avoid formula<->ingredient cycle
}


def gid():
    return str(uuid.uuid4())


def col_tmdl(name, dtype):
    summ = "sum" if dtype in ("int64", "double", "decimal") else "none"
    lines = [f"\tcolumn {name}",
             f"\t\tdataType: {dtype}",
             f"\t\tsourceColumn: {name}",
             f"\t\tlineageTag: {gid()}",
             f"\t\tsummarizeBy: {summ}"]
    if dtype == "dateTime":
        lines.insert(2, "\t\tformatString: General Date")
    return "\n".join(lines)


def table_tmdl(t):
    cols = "\n\n".join(col_tmdl(n, d) for n, d in schemas[t])
    return (f"table {t}\n"
            f"\tlineageTag: {gid()}\n\n"
            f"{cols}\n\n"
            f"\tpartition {t} = entity\n"
            f"\t\tmode: directLake\n"
            f"\t\tsource\n"
            f"\t\t\tentityName: {t}\n"
            f"\t\t\tschemaName: dbo\n"
            f"\t\t\texpressionSource: DatabaseQuery\n")


def rels_tmdl():
    blocks = []
    for ft, fc, tt, tc in RELS:
        block = (f"relationship {gid()}\n"
                 f"\tfromColumn: {ft}.{fc}\n"
                 f"\ttoColumn: {tt}.{tc}\n")
        if (ft, fc) in INACTIVE:
            block += "\tisActive: false\n"
        blocks.append(block)
    return "\n".join(blocks)


expr_tmdl = (
    "expression DatabaseQuery =\n"
    "\t\tlet\n"
    f'\t\t\tSource = Sql.Database("{SQL_SERVER}", "{SQL_DB}")\n'
    "\t\tin\n"
    "\t\t\tSource\n"
    "\tlineageTag: " + gid() + "\n"
    "\tannotation PBI_ResultType = Table\n"
)

model_refs = "\n".join(f"ref table {t}" for t in TABLES)
model_tmdl = (
    "model Model\n"
    "\tculture: en-US\n"
    "\tdefaultPowerBIDataSourceVersion: powerBI_V3\n"
    "\tdiscourageImplicitMeasures\n"
    "\tsourceQueryCulture: en-US\n"
    "\tdataAccessOptions\n"
    "\t\tlegacyRedirects\n"
    "\t\treturnErrorValuesAsNull\n\n"
    'annotation PBI_QueryOrder = ["DatabaseQuery"]\n\n'
    "annotation __PBI_TimeIntelligenceEnabled = 0\n\n"
    f"{model_refs}\n"
)

database_tmdl = "database\n\tcompatibilityLevel: 1604\n"
pbism = json.dumps({"version": "4.0", "settings": {}})


def b64(s):
    return base64.b64encode(s.encode("utf-8")).decode("ascii")


parts = [
    {"path": "definition.pbism", "payload": b64(pbism), "payloadType": "InlineBase64"},
    {"path": "definition/database.tmdl", "payload": b64(database_tmdl), "payloadType": "InlineBase64"},
    {"path": "definition/model.tmdl", "payload": b64(model_tmdl), "payloadType": "InlineBase64"},
    {"path": "definition/expressions.tmdl", "payload": b64(expr_tmdl), "payloadType": "InlineBase64"},
    {"path": "definition/relationships.tmdl", "payload": b64(rels_tmdl()), "payloadType": "InlineBase64"},
]
for t in TABLES:
    parts.append({"path": f"definition/tables/{t}.tmdl",
                  "payload": b64(table_tmdl(t)), "payloadType": "InlineBase64"})

body = {"displayName": NAME,
        "description": "Constanto pharmaceutical-compounding ontology: 15 connected entities with supplier-to-patient traceability relationships (DirectLake over ConstantoLakehouse).",
        "definition": {"parts": parts}}

H = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}
r = requests.post(f"https://api.fabric.microsoft.com/v1/workspaces/{WS}/semanticModels",
                  headers=H, json=body, timeout=120)
print("POST status:", r.status_code)
if r.status_code == 202:
    loc = r.headers.get("Location")
    print("polling:", loc)
    for _ in range(30):
        time.sleep(5)
        p = requests.get(loc, headers=H, timeout=60)
        st = p.json().get("status")
        print("  status:", st)
        if st in ("Succeeded", "Failed"):
            print(json.dumps(p.json(), indent=2)[:1500])
            break
elif r.status_code in (200, 201):
    print(json.dumps(r.json(), indent=2)[:1000])
else:
    print(r.text[:2000])
