import pandas as pd

PREDICTION_FILE = "data/processed/plant_ai_predictions.csv"
PLANT_FILE = "data/raw/medicinal_plants.csv"
UNIPROT_FILE = "data/processed/uniprot_details.csv"

OUTPUT_FILE = "data/processed/plant_ai_annotated.csv"


print("========================================")
print("AI 예측 데이터 불러오기")
print("========================================")

prediction = pd.read_csv(PREDICTION_FILE)

print("AI 예측:", len(prediction))


print()
print("========================================")
print("표준 식물 데이터 불러오기")
print("========================================")

plants = pd.read_csv(PLANT_FILE)

print("표준 식물:", len(plants))


print()
print("========================================")
print("UniProt 데이터 불러오기")
print("========================================")

uniprot = pd.read_csv(UNIPROT_FILE)

print("UniProt:", len(uniprot))


# --------------------------------------------------
# Plant_ID 기준 표준 식물명 연결
# --------------------------------------------------

plant_columns = [
    "Plant_ID",
    "Common_Name_KO",
    "English_Name",
    "Scientific_Name"
]

plants = plants[plant_columns].copy()

prediction = prediction.drop(
    columns=[
        "Scientific_Name"
    ],
    errors="ignore"
)

prediction = prediction.merge(
    plants,
    on="Plant_ID",
    how="left",
    validate="many_to_one"
)


print()
print("========================================")
print("표준 식물명 연결")
print("========================================")

print(
    "식물명 미연결:",
    prediction["Scientific_Name"].isna().sum()
)


# --------------------------------------------------
# UniProt 단백질 정보 연결
# --------------------------------------------------

uniprot_columns = [
    "UniProt_ID",
    "Protein_Name",
    "Gene_Name",
    "Organism",
    "Reviewed"
]

available_columns = [
    column
    for column in uniprot_columns
    if column in uniprot.columns
]

uniprot = uniprot[available_columns].copy()

uniprot = uniprot.drop_duplicates(
    subset=["UniProt_ID"]
)

prediction = prediction.merge(
    uniprot,
    on="UniProt_ID",
    how="left",
    validate="many_to_one"
)


print()
print("========================================")
print("UniProt 정보 연결")
print("========================================")

print(
    "단백질명 미연결:",
    prediction["Protein_Name"].isna().sum()
)

print(
    "유전자명 미연결:",
    prediction["Gene_Name"].isna().sum()
)

print(
    "생물종 미연결:",
    prediction["Organism"].isna().sum()
)


# --------------------------------------------------
# 기본 검증
# --------------------------------------------------

print()
print("========================================")
print("최종 데이터 검증")
print("========================================")

print(
    "전체 행:",
    len(prediction)
)

print(
    "식물:",
    prediction["Plant_ID"].nunique()
)

print(
    "화합물:",
    prediction["ChEMBL_ID"].nunique()
)

print(
    "UniProt:",
    prediction["UniProt_ID"].nunique()
)

print(
    "표준 학명:",
    prediction["Scientific_Name"].nunique()
)


# --------------------------------------------------
# 표준 학명 목록 확인
# --------------------------------------------------

print()
print("========================================")
print("표준 학명")
print("========================================")

print(
    prediction[
        [
            "Plant_ID",
            "Common_Name_KO",
            "English_Name",
            "Scientific_Name"
        ]
    ]
    .drop_duplicates()
    .sort_values("Plant_ID")
    .to_string(index=False)
)


# --------------------------------------------------
# 결과 저장
# --------------------------------------------------

prediction.to_csv(
    OUTPUT_FILE,
    index=False,
    encoding="utf-8-sig"
)


print()
print("========================================")
print("분석용 데이터 저장 완료")
print("========================================")

print(
    "파일:",
    OUTPUT_FILE
)