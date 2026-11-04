import pandas as pd


PLANT_FILE = "data/processed/plant_compounds_chembl.csv"
ML_FILE = "data/processed/ml_dataset.csv"

OUTPUT_FILE = "data/processed/plant_ai_connection.csv"


# ==================================================
# 1. 데이터 불러오기
# ==================================================

plant = pd.read_csv(PLANT_FILE)
ml = pd.read_csv(ML_FILE)

print("========================================")
print("데이터 불러오기")
print("========================================")
print("식물-화합물-ChEMBL 데이터:", len(plant))
print("AI ML 데이터:", len(ml))


# ==================================================
# 2. ChEMBL ID가 있는 식물 화합물만 확인
# ==================================================

plant_chembl = plant[
    plant["ChEMBL_ID"].notna()
].copy()

print()
print("========================================")
print("식물 화합물의 ChEMBL 연결")
print("========================================")
print("전체 식물 화합물:", len(plant))
print("ChEMBL 연결 성공:", len(plant_chembl))
print(
    "고유 ChEMBL 화합물:",
    plant_chembl["ChEMBL_ID"].nunique()
)


# ==================================================
# 3. AI 모델에서 사용된 ChEMBL 화합물
# ==================================================

ml_chembl = set(
    ml["ChEMBL_ID"]
    .dropna()
    .unique()
)

print()
print("========================================")
print("AI 모델 화합물")
print("========================================")
print(
    "AI 모델 고유 ChEMBL:",
    len(ml_chembl)
)


# ==================================================
# 4. 식물 화합물과 AI 화합물의 교집합
# ==================================================

plant_chembl_set = set(
    plant_chembl["ChEMBL_ID"]
    .dropna()
    .unique()
)

common_chembl = (
    plant_chembl_set
    & ml_chembl
)

print()
print("========================================")
print("식물 ↔ AI 화합물 연결")
print("========================================")
print(
    "식물 데이터 ChEMBL:",
    len(plant_chembl_set)
)

print(
    "AI 데이터 ChEMBL:",
    len(ml_chembl)
)

print(
    "공통 ChEMBL:",
    len(common_chembl)
)


# ==================================================
# 5. 실제 연결 데이터 생성
# ==================================================

connection = plant_chembl[
    plant_chembl["ChEMBL_ID"].isin(common_chembl)
].copy()

print()
print("========================================")
print("최종 식물 ↔ AI 연결 데이터")
print("========================================")
print(
    "연결 행:",
    len(connection)
)

print(
    "연결된 고유 식물:",
    connection["Plant_ID"].nunique()
)

print(
    "연결된 고유 ChEMBL:",
    connection["ChEMBL_ID"].nunique()
)


# ==================================================
# 6. 식물별 연결 현황
# ==================================================

plant_summary = (
    connection
    .groupby(
        [
            "Plant_ID",
            "Scientific_Name"
        ]
    )
    .agg(
        Connected_Compounds=(
            "ChEMBL_ID",
            "nunique"
        )
    )
    .reset_index()
)

print()
print("========================================")
print("식물별 AI 연결 화합물")
print("========================================")

print(
    plant_summary.to_string(index=False)
)


# ==================================================
# 7. AI 모델 데이터와 연결
# ==================================================

ai_info = ml[
    [
        "ChEMBL_ID",
        "UniProt_ID",
        "Standard_Type",
        "pChEMBL"
    ]
].copy()

ai_info = ai_info[
    ai_info["ChEMBL_ID"].isin(common_chembl)
].copy()

print()
print("========================================")
print("식물 ↔ 화합물 ↔ 단백질 연결")
print("========================================")

print(
    "AI 연결 행:",
    len(ai_info)
)

print(
    "연결된 ChEMBL:",
    ai_info["ChEMBL_ID"].nunique()
)

print(
    "연결된 UniProt:",
    ai_info["UniProt_ID"].nunique()
)


# ==================================================
# 8. 식물-화합물-단백질 최종 테이블
# ==================================================

final = connection[
    [
        "Plant_ID",
        "Scientific_Name",
        "KNApSAcK_ID",
        "Compound_Name",
        "ChEMBL_ID"
    ]
].drop_duplicates()

final = final.merge(
    ai_info,
    on="ChEMBL_ID",
    how="left"
)

print()
print("========================================")
print("최종 GeoPharm 연결 구조")
print("========================================")
print(
    "행:",
    len(final)
)

print(
    "식물:",
    final["Plant_ID"].nunique()
)

print(
    "화합물:",
    final["ChEMBL_ID"].nunique()
)

print(
    "단백질:",
    final["UniProt_ID"].nunique()
)


# ==================================================
# 9. 저장
# ==================================================

final.to_csv(
    OUTPUT_FILE,
    index=False,
    encoding="utf-8-sig"
)

print()
print("========================================")
print("저장 완료")
print("========================================")
print(
    "파일:",
    OUTPUT_FILE
)