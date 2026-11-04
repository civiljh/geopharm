import requests
import pandas as pd
from rdkit import Chem
from rdkit.Chem import inchi


UNIPROT_ID = "P00533"
OUTPUT_FILE = "data/processed/bindingdb_egfr_with_inchikey.csv"


print("BindingDB 데이터 다운로드 중...")

url = (
    "https://bindingdb.org/rest/"
    "getLigandsByUniprot"
)

params = {
    "uniprot": UNIPROT_ID,
    "response": "application/json"
}

response = requests.get(
    url,
    params=params,
    timeout=60
)

response.raise_for_status()

data = response.json()

records = data["getLindsByUniprotResponse"]["bdb.affinities"]

print("BindingDB 원본 데이터:", len(records))
print()


def smiles_to_inchikey(smiles):
    try:
        if not smiles:
            return None

        mol = Chem.MolFromSmiles(smiles)

        if mol is None:
            return None

        return inchi.MolToInchiKey(mol)

    except Exception:
        return None


rows = []

for number, record in enumerate(records, start=1):

    smiles = record.get("bdb.smile")

    inchikey = smiles_to_inchikey(smiles)

    rows.append({
        "UniProt_ID": UNIPROT_ID,
        "Monomer_ID": record.get("bdb.monomerid"),
        "SMILES": smiles,
        "InChIKey": inchikey,
        "Affinity_Type": record.get("bdb.affinity_type"),
        "Affinity": record.get("bdb.affinity")
    })

    if number % 500 == 0:
        print(f"{number}/{len(records)} 처리 완료")


df = pd.DataFrame(rows)


print()
print("==============================")
print("BindingDB InChIKey 생성 완료")
print("==============================")
print("전체 데이터:", len(df))
print("InChIKey 생성 성공:", df["InChIKey"].notna().sum())
print("InChIKey 생성 실패:", df["InChIKey"].isna().sum())


df.to_csv(
    OUTPUT_FILE,
    index=False,
    encoding="utf-8-sig"
)

print()
print("저장 파일:", OUTPUT_FILE)