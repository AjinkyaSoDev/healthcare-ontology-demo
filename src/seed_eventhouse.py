"""Seed the ConstantoEventhouse KQL database with the two time-series tables,
ingesting directly from OneLake via impersonation."""
import sys
import time
import requests

QUERY_URI = "https://trd-x96m92hee4fp0quzjr.z6.kusto.fabric.microsoft.com"
DB = "ConstantoEventhouse"
WS = "<WORKSPACE_ID>"
LH = "<LAKEHOUSE_ID>"
token = sys.argv[1]
H = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def mgmt(csl):
    r = requests.post(f"{QUERY_URI}/v1/rest/mgmt", headers=H,
                      json={"db": DB, "csl": csl}, timeout=120)
    if r.status_code != 200:
        print("ERR", r.status_code, r.text[:500])
        r.raise_for_status()
    return r.json()


def query(csl):
    r = requests.post(f"{QUERY_URI}/v1/rest/query", headers=H,
                      json={"db": DB, "csl": csl}, timeout=120)
    r.raise_for_status()
    return r.json()


def onelake(path):
    return f"https://onelake.blob.fabric.microsoft.com/{WS}/{LH}/Files/raw/{path};impersonate"


# 1) create tables
mgmt(""".create table cleanroom_sensor_reading (
    timestamp: datetime, room_id: string, temperature_c: real,
    humidity_pct: real, particle_count_0_5um: long, diff_pressure_pa: real)""")
mgmt(""".create table stability_reading (
    timestamp: datetime, batch_id: string, month: int,
    assay_percent: real, impurity_percent: real, storage_condition: string)""")
print("tables created")

# 2) ingest from OneLake (inline, synchronous)
mgmt(f""".ingest into table cleanroom_sensor_reading (h'{onelake("cleanroom_sensor_reading.csv")}')
    with (format='csv', ignoreFirstRecord=true)""")
print("cleanroom_sensor_reading ingested")
mgmt(f""".ingest into table stability_reading (h'{onelake("stability_reading.csv")}')
    with (format='csv', ignoreFirstRecord=true)""")
print("stability_reading ingested")

time.sleep(3)
# 3) verify counts
for t in ("cleanroom_sensor_reading", "stability_reading"):
    res = query(f"{t} | count")
    n = res["Tables"][0]["Rows"][0][0]
    print(f"{t}: {n} rows")
