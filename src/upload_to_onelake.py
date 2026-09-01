"""Upload generated CSVs to the Fabric Lakehouse Files area via the OneLake ADLS Gen2 API.

Usage:
  python src/upload_to_onelake.py <storage_token> <workspaceId> <lakehouseId>
"""
import os
import sys
import glob
import requests

token = sys.argv[1]
workspace = sys.argv[2]
lakehouse = sys.argv[3]

DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
BASE = f"https://onelake.dfs.fabric.microsoft.com/{workspace}/{lakehouse}"
H = {"Authorization": f"Bearer {token}"}

def upload(local_path: str, rel_path: str):
    url = f"{BASE}/Files/{rel_path}"
    # 1) create empty file
    r = requests.put(url + "?resource=file", headers=H, timeout=60)
    if r.status_code not in (201, 202):
        print("CREATE FAIL", rel_path, r.status_code, r.text[:200]); return False
    data = open(local_path, "rb").read()
    # 2) append content at offset 0
    r = requests.patch(url + "?action=append&position=0",
                       headers={**H, "Content-Type": "application/octet-stream"},
                       data=data, timeout=120)
    if r.status_code not in (200, 202):
        print("APPEND FAIL", rel_path, r.status_code, r.text[:200]); return False
    # 3) flush
    r = requests.patch(url + f"?action=flush&position={len(data)}", headers=H, timeout=60)
    if r.status_code not in (200, 202):
        print("FLUSH FAIL", rel_path, r.status_code, r.text[:200]); return False
    print(f"uploaded raw/{rel_path} ({len(data)} bytes)")
    return True

ok = 0
for f in sorted(glob.glob(os.path.join(DATA, "*.csv"))):
    name = os.path.basename(f)
    if upload(f, f"raw/{name}"):
        ok += 1
print(f"\nDone: {ok} files uploaded to Files/raw/")
