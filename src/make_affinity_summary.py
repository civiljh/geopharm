import pandas as pd

INPUT_FILE = "data/processed/final_target_affinity.csv"
OUTPUT_FILE = "data/processed/affinity_summary.csv"

df = pd.read_csv(INPUT_FILE)

print("원본 레코드:", len(df))
print()

group_columns = [
    "Plant_ID",
    "KNApSAcK_ID",
    "Compound_Name",
    "Chemical_InChIKey",
    "ChEMBL_ID",
    "UniProt_ID",
    "Protein_Name",
    "Gene_Name",
    "Organism",
    "Standard_Type"
]

summary = (
    df.groupby(group_columns, dropna=False)
    .agg(
        Standard_Value_Median=("Standard_Value", "median"),
        pChEMBL_Median=("pChEMBL_Value", "median"),
        pChEMBL_Min=("pChEMBL_Value", "min"),
        pChEMBL_Max=("pChEMBL_Value", "max"),
        Assay_Count=("Activity_ID", "count")
    )
    .reset_index()
)

print("================================")
print("Affinity 요약 데이터 생성 완료")
print("================================")
print("원본 레코드:", len(df))
print("요약 레코드:", len(summary))
print("줄어든 중복 레코드:", len(df) - len(summary))
print()

print("측정 타입별 요약 레코드:")
print(
    summary["Standard_Type"]
    .value_counts()
    .to_string()
)

print()

print("Assay 횟수 통계:")
print(
    summary["Assay_Count"]
    .describe()
    .to_string()
)

summary.to_csv(
    OUTPUT_FILE,
    index=False,
    encoding="utf-8-sig"
)

print()
print("저장 파일:", OUTPUT_FILE)