import pandas as pd
from rdkit import Chem
from rdkit.Chem import inchi

# BindingDB 데이터 읽기
df = pd.read_csv(
    "data/raw/bindingdb_test.csv"
)

# SMILES를 InChIKey로 변환하는 함수
def smiles_to_inchikey(smiles):
    try:
        if pd.isna(smiles):
            return None

        mol = Chem.MolFromSmiles(smiles)

        if mol is None:
            return None

        return inchi.MolToInchiKey(mol)

    except Exception:
        return None


# 전체 화합물의 InChIKey 생성
df["InChIKey"] = df["SMILES"].apply(smiles_to_inchikey)

# 결과 확인
print("전체 데이터 개수:", len(df))
print("InChIKey 생성 성공:", df["InChIKey"].notna().sum())
print("InChIKey 생성 실패:", df["InChIKey"].isna().sum())

print()
print(df.head())

# 새로운 파일로 저장
df.to_csv(
    "data/processed/bindingdb_with_inchikey.csv",
    index=False,
    encoding="utf-8-sig"
)

print()
print("bindingdb_with_inchikey.csv 저장 완료")