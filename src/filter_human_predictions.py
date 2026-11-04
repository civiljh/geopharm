import pandas as pd

INPUT_FILE = "data/processed/plant_ai_annotated.csv"
OUTPUT_FILE = "data/processed/plant_ai_human_predictions.csv"


print("========================================")
print("AI 예측 데이터 불러오기")
print("========================================")

df = pd.read_csv(INPUT_FILE)

print("전체 예측:", len(df))


# --------------------------------------------------
# 사람(Homo sapiens) 단백질만 선택
# --------------------------------------------------

human = df[
    df["Organism"].astype(str).str.strip()
    == "Homo sapiens"
].copy()


print()
print("========================================")
print("사람 단백질 필터링")
print("========================================")

print(
    "사람 단백질 예측:",
    len(human)
)

print(
    "식물:",
    human["Plant_ID"].nunique()
)

print(
    "화합물:",
    human["ChEMBL_ID"].nunique()
)

print(
    "UniProt:",
    human["UniProt_ID"].nunique()
)


# --------------------------------------------------
# 데이터 무결성 확인
# --------------------------------------------------

print()
print("========================================")
print("데이터 검증")
print("========================================")

print(
    "사람 단백질 외 데이터:",
    (
        human["Organism"]
        .astype(str)
        .str.strip()
        .ne("Homo sapiens")
        .sum()
    )
)

print(
    "단백질명 미연결:",
    human["Protein_Name"].isna().sum()
)

print(
    "유전자명 미연결:",
    human["Gene_Name"].isna().sum()
)


# --------------------------------------------------
# 식물별 사람 단백질 수
# --------------------------------------------------

plant_summary = (
    human
    .groupby(
        [
            "Plant_ID",
            "Common_Name_KO",
            "Scientific_Name"
        ],
        as_index=False
    )
    .agg(
        Compounds=(
            "ChEMBL_ID",
            "nunique"
        ),
        Human_Proteins=(
            "UniProt_ID",
            "nunique"
        ),
        Prediction_Rows=(
            "UniProt_ID",
            "size"
        )
    )
    .sort_values("Plant_ID")
)


print()
print("========================================")
print("식물별 사람 단백질")
print("========================================")

print(
    plant_summary.to_string(index=False)
)


# --------------------------------------------------
# 저장
# --------------------------------------------------

human.to_csv(
    OUTPUT_FILE,
    index=False,
    encoding="utf-8-sig"
)


print()
print("========================================")
print("사람 단백질 데이터 저장 완료")
print("========================================")

print(
    "파일:",
    OUTPUT_FILE
)