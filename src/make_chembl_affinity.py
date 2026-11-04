import pandas as pd


INPUT_FILE = "data/processed/chembl_activity.csv"
OUTPUT_FILE = "data/processed/chembl_affinity.csv"


df = pd.read_csv(INPUT_FILE)


print("전체 Activity:", len(df))
print()


# ML에 사용할 주요 affinity / potency 측정값
allowed_types = [
    "IC50",
    "Ki",
    "Kd",
    "EC50",
    "AC50",
    "Potency"
]


affinity = df[
    df["Standard_Type"].isin(allowed_types)
].copy()


print("허용된 Standard_Type:")
print(
    affinity["Standard_Type"]
    .value_counts()
    .to_string()
)

print()


# 숫자로 변환할 수 없는 값 제거
affinity["Standard_Value"] = pd.to_numeric(
    affinity["Standard_Value"],
    errors="coerce"
)

affinity["pChEMBL"] = pd.to_numeric(
    affinity["pChEMBL"],
    errors="coerce"
)


# 실제 측정값과 pChEMBL이 모두 존재하는 데이터만 사용
affinity = affinity[
    affinity["Standard_Value"].notna()
    & affinity["pChEMBL"].notna()
].copy()


# 정확히 측정된 값만 사용
affinity = affinity[
    affinity["Standard_Relation"].fillna("=") == "="
].copy()


print("================================")
print("Affinity 데이터 정제 완료")
print("================================")

print(
    "정제 후 데이터:",
    len(affinity)
)

print(
    "pChEMBL 존재:",
    affinity["pChEMBL"].notna().sum()
)

print()


print("Standard_Type:")
print(
    affinity["Standard_Type"]
    .value_counts()
    .to_string()
)

print()


print(
    "고유 화합물:",
    affinity["ChEMBL_ID"].nunique()
)

print(
    "고유 표적:",
    affinity["Target_ChEMBL_ID"].nunique()
)


affinity.to_csv(
    OUTPUT_FILE,
    index=False,
    encoding="utf-8-sig"
)


print()
print("저장 파일:", OUTPUT_FILE)