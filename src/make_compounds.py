import pandas as pd

# 1. PubChem 데이터 읽기
pubchem = pd.read_csv(
    "data/raw/pubchem_test.csv"
)

# 2. ChEMBL 데이터 읽기
chembl = pd.read_csv(
    "data/raw/chembl_test.csv"
)

# 3. InChIKey를 기준으로 두 데이터를 연결
compounds = pd.merge(
    pubchem,
    chembl,
    on="InChIKey",
    how="outer",
    suffixes=("_PubChem", "_ChEMBL")
)

# 4. 결과 확인
print("통합된 화합물 개수:", len(compounds))
print()
print(compounds)

# 5. 통합 데이터 저장
compounds.to_csv(
    "data/processed/compounds.csv",
    index=False,
    encoding="utf-8-sig"
)

print()
print("compounds.csv 저장 완료")