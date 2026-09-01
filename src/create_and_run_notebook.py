"""Create and run a Fabric notebook that loads Files/raw/*.csv into Delta tables.

Usage:
  python src/create_and_run_notebook.py <fabric_token> <workspaceId> <lakehouseId> <lakehouseName>
"""
import base64
import json
import sys
import time
import requests

token = sys.argv[1]
ws = sys.argv[2]
lh = sys.argv[3]
lh_name = sys.argv[4]

H = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
API = "https://api.fabric.microsoft.com/v1"

load_code = (
    "tables = [\n"
    "    'site','cleanroom','equipment','supplier','ingredient','formula',\n"
    "    'formula_ingredient','operator','prescriber','patient','raw_material_lot',\n"
    "    'batch','batch_raw_material_lot','prescription','quality_test',\n"
    "    'cleanroom_sensor_reading','stability_reading']\n"
    "for t in tables:\n"
    "    df = (spark.read.option('header', True).option('inferSchema', True)\n"
    "          .csv(f'Files/raw/{t}.csv'))\n"
    "    df.write.mode('overwrite').format('delta').option('overwriteSchema','true').saveAsTable(t)\n"
    "    print('loaded', t, df.count())\n"
    "print('ALL TABLES LOADED')\n"
)

notebook = {
    "nbformat": 4,
    "nbformat_minor": 5,
    "cells": [
        {"cell_type": "code", "source": load_code.splitlines(keepends=True),
         "execution_count": None, "outputs": [], "metadata": {}},
    ],
    "metadata": {
        "language_info": {"name": "python"},
        "dependencies": {
            "lakehouse": {
                "default_lakehouse": lh,
                "default_lakehouse_name": lh_name,
                "default_lakehouse_workspace_id": ws,
            }
        },
    },
}

payload = base64.b64encode(json.dumps(notebook).encode("utf-8")).decode("utf-8")
body = {
    "displayName": "Load_Constanto_Tables",
    "definition": {
        "format": "ipynb",
        "parts": [
            {"path": "notebook-content.ipynb", "payload": payload,
             "payloadType": "InlineBase64"}
        ],
    },
}

print("Creating notebook...")
r = requests.post(f"{API}/workspaces/{ws}/notebooks", headers=H, json=body, timeout=120)
if r.status_code in (201, 202):
    # 202 -> LRO; poll the operation location
    if r.status_code == 202:
        op = r.headers.get("Location")
        while True:
            time.sleep(5)
            s = requests.get(op, headers=H, timeout=60).json()
            if s.get("status") in ("Succeeded", "Failed"):
                break
        nb = requests.get(op + "/result", headers=H, timeout=60).json() if s.get("status") == "Succeeded" else {}
        nb_id = nb.get("id")
    else:
        nb_id = r.json().get("id")
    print("Notebook id:", nb_id)
else:
    print("Create failed:", r.status_code, r.text[:400]); sys.exit(1)

print("Running notebook...")
run = requests.post(
    f"{API}/workspaces/{ws}/items/{nb_id}/jobs/instances?jobType=RunNotebook",
    headers=H, timeout=120)
if run.status_code not in (200, 202):
    print("Run trigger failed:", run.status_code, run.text[:400]); sys.exit(1)
job_url = run.headers.get("Location")
print("Job started, polling...")
for _ in range(60):
    time.sleep(10)
    st = requests.get(job_url, headers=H, timeout=60).json()
    status = st.get("status")
    print("  status:", status)
    if status in ("Completed", "Failed", "Cancelled", "Deduped"):
        break
print("FINAL:", status)
print("notebook_id=" + str(nb_id))
