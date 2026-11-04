import requests
import pandas as pd

url = "https://www.ebi.ac.uk/chembl/api/data/molecule/CHEMBL25.json"

response = requests.get(url)

print("HTTP 상태 코드:", response.status_code)
response.raise_for_status()

data = response.json()

molecule_id = data.get("molecule_chembl_id")
pref_name = data.get("pref_name")

properties = data.get("molecule_properties", {})
structures = data.get("molecule_structures", {})

result = {
    "ChEMBL_ID": molecule_id,
    "Name": pref_name,
    "MolecularFormula": properties.get("full_molformula"),
    "MolecularWeight": properties.get("full_mwt"),
    "AlogP": properties.get("alogp"),
    "HBA": properties.get("hba"),
    "HBD": properties.get("hbd"),
    "PSA": properties.get("psa"),
    "QED": properties.get("qed_weighted"),
    "CanonicalSMILES": structures.get("canonical_smiles"),
    "InChI": structures.get("standard_inchi"),
    "InChIKey": structures.get("standard_inchi_key")
}

df = pd.DataFrame([result])

print(df)

df.to_csv(
    "data/raw/chembl_test.csv",
    index=False,
    encoding="utf-8-sig"
)

print("ChEMBL CSV 저장 완료")