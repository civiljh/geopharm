import requests
import pandas as pd
from io import StringIO

url = (
    "https://pubchem.ncbi.nlm.nih.gov/rest/pug/"
    "compound/cid/2244/property/"
    "MolecularFormula,MolecularWeight,CanonicalSMILES,IsomericSMILES,InChIKey/"
    "CSV"
)

response = requests.get(url)

print("HTTP 상태 코드:", response.status_code)
response.raise_for_status()

df = pd.read_csv(StringIO(response.text))

print(df)

df.to_csv(
    "data/raw/pubchem_test.csv",
    index=False,
    encoding="utf-8-sig"
)

print("PubChem 데이터 저장 완료")