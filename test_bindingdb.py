import requests
import pandas as pd

uniprot_id = "P00533"

url = (
    "https://bindingdb.org/rest/"
    f"getLigandsByUniprot?uniprot={uniprot_id}"
    "&response=application/json"
)

response = requests.get(url)

print("HTTP 상태 코드:", response.status_code)
response.raise_for_status()

data = response.json()

result = data["getLindsByUniprotResponse"]

affinities = result.get("bdb.affinities", [])

rows = []

for item in affinities:
    rows.append({
        "UniProt_ID": result.get("bdb.primary"),
        "Monomer_ID": item.get("bdb.monomerid"),
        "SMILES": item.get("bdb.smile"),
        "Affinity_Type": item.get("bdb.affinity_type"),
        "Affinity": item.get("bdb.affinity")
    })

df = pd.DataFrame(rows)

print("가져온 데이터 개수:", len(df))
print(df.head())

df.to_csv(
    "data/raw/bindingdb_test.csv",
    index=False,
    encoding="utf-8-sig"
)

print("BindingDB CSV 저장 완료")