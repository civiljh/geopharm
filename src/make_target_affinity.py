import pandas as pd

AFFINITY_FILE = "data/processed/chembl_affinity.csv"
TARGET_FILE = "data/processed/chembl_targets.csv"
OUTPUT_FILE = "data/processed/target_affinity.csv"

print("파일 읽는 중...")

affinity = pd.read_csv(AFFINITY_FILE)
targets = pd.read_csv(TARGET_FILE)

print("Affinity 레코드:", len(affinity))
print("Target 레코드:", len(targets))
print()

# Target 정보 중 필요한 열만 사용
target_columns = [
    "Target_ChEMBL_ID",
    "Target_Name",
    "Target_Organism",
    "Target_Type",
    "UniProt_ID",
    "Component_Type",
    "Relationship",
    "Target_Status"
]

targets = targets[target_columns]

# ChEMBL Target ID를 기준으로 연결
merged = affinity.merge(
    targets,
    on="Target_ChEMBL_ID",
    how="left",
    suffixes=("_Activity", "_Target")
)

print("================================")
print("Target + Affinity 통합 완료")
print("================================")
print("전체 Activity:", len(merged))

print(
    "PROTEIN Activity:",
    (merged["Target_Status"] == "PROTEIN").sum()
)

print(
    "UniProt 연결 Activity:",
    merged["UniProt_ID"].notna().sum()
)

print(
    "UniProt 미연결 Activity:",
    merged["UniProt_ID"].isna().sum()
)

print()

# 실제 단백질 표적만 별도 저장
protein_df = merged[
    merged["Target_Status"] == "PROTEIN"
].copy()

protein_df.to_csv(
    OUTPUT_FILE,
    index=False,
    encoding="utf-8-sig"
)

print("최종 단백질-활성 데이터:", len(protein_df))
print("저장 파일:", OUTPUT_FILE)