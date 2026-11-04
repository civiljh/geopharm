import pandas as pd
from rdkit import Chem
from rdkit.Chem import inchi


INPUT_FILE = "data/raw/plant_compounds_structures.csv"
OUTPUT_FILE = "data/raw/plant_compounds_with_inchikey.csv"


df = pd.read_csv(INPUT_FILE)


def smiles_to_inchikey(smiles):
    try:
        if pd.isna(smiles):
            return None

        mol = Chem.MolFromSmiles(str(smiles))

        if mol is None:
            return None

        return inchi.MolToInchiKey(mol)

    except Exception:
        return None


print("전체 데이터:", len(df))
print()


# KNApSAcK SMILES → RDKit InChIKey
df["KNApSAcK_InChIKey"] = (
    df["KNApSAcK_SMILES"]
    .apply(smiles_to_inchikey)
)


print(
    "RDKit InChIKey 생성 성공:",
    df["KNApSAcK_InChIKey"].notna().sum()
)

print(
    "RDKit InChIKey 생성 실패:",
    df["KNApSAcK_InChIKey"].isna().sum()
)

print()


# PubChem InChIKey와 비교
def compare_inchikey(row):

    pubchem_key = row["InChIKey"]
    knapsack_key = row["KNApSAcK_InChIKey"]

    if pd.isna(knapsack_key):
        return "KNApSAcK_KEY 없음"

    if pd.isna(pubchem_key):
        return "PubChem_KEY 없음"

    if str(pubchem_key) == str(knapsack_key):
        return "MATCH"

    return "MISMATCH"


df["InChIKey_Check"] = df.apply(
    compare_inchikey,
    axis=1
)


print("================================")
print("InChIKey 비교 결과")
print("================================")

print(
    df["InChIKey_Check"]
    .value_counts(dropna=False)
)

print()


# 실제 불일치만 표시
mismatch = df[
    df["InChIKey_Check"] == "MISMATCH"
]

print(
    "PubChem과 InChIKey가 다른 물질:",
    len(mismatch)
)

if len(mismatch) > 0:

    print()

    print(
        mismatch[
            [
                "KNApSAcK_ID",
                "Compound_Name",
                "InChIKey",
                "KNApSAcK_InChIKey",
            ]
        ].to_string(index=False)
    )


# 저장
df.to_csv(
    OUTPUT_FILE,
    index=False,
    encoding="utf-8-sig"
)


print()
print("================================")
print("InChIKey 생성 및 검증 완료")
print("================================")
print("저장 파일:", OUTPUT_FILE)