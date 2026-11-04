import pandas as pd

INPUT_FILE = "data/processed/plant_ai_human_predictions.csv"
OUTPUT_FILE = "data/processed/human_target_list.csv"


print("========================================")
print("사람 단백질 예측 데이터 불러오기")
print("========================================")

df = pd.read_csv(INPUT_FILE)

print("전체 예측:", len(df))


# --------------------------------------------------
# 단백질별 고유 목록 생성
# --------------------------------------------------

target_columns = [
    "UniProt_ID",
    "Protein_Name",
    "Gene_Name",
    "Organism",
    "Reviewed"
]

targets = (
    df[target_columns]
    .drop_duplicates(
        subset=["UniProt_ID"]
    )
    .sort_values("UniProt_ID")
    .reset_index(drop=True)
)


print()
print("========================================")
print("사람 단백질 목록")
print("========================================")

print(
    "고유 UniProt:",
    len(targets)
)


# --------------------------------------------------
# 데이터 검증
# --------------------------------------------------

print()
print("========================================")
print("단백질 정보 검증")
print("========================================")

print(
    "UniProt ID 미연결:",
    targets["UniProt_ID"].isna().sum()
)

print(
    "Protein Name 미연결:",
    targets["Protein_Name"].isna().sum()
)

print(
    "Gene Name 미연결:",
    targets["Gene_Name"].isna().sum()
)

print(
    "Organism 미연결:",
    targets["Organism"].isna().sum()
)

print(
    "Reviewed 미연결:",
    targets["Reviewed"].isna().sum()
)

print(
    "Homo sapiens:",
    (
        targets["Organism"].astype(str).str.strip()
        == "Homo sapiens"
    ).sum()
)


# --------------------------------------------------
# 처음 30개 확인
# --------------------------------------------------

print()
print("========================================")
print("단백질 목록 일부")
print("========================================")

print(
    targets.head(30).to_string(index=False)
)


# --------------------------------------------------
# 저장
# --------------------------------------------------

targets.to_csv(
    OUTPUT_FILE,
    index=False,
    encoding="utf-8-sig"
)


print()
print("========================================")
print("단백질 목록 저장 완료")
print("========================================")

print(
    "파일:",
    OUTPUT_FILE
)