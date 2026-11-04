import pandas as pd


PLANT_FILE = "data/processed/plant_compounds_chembl.csv"
RDKIT_FILE = "data/processed/rdkit_features.csv"

OUTPUT_FILE = "data/processed/plant_ai_prediction_ready.csv"


# ==================================================
# 1. 데이터 불러오기
# ==================================================

plant = pd.read_csv(PLANT_FILE)
rdkit = pd.read_csv(RDKIT_FILE)

print("========================================")
print("데이터 불러오기")
print("========================================")
print("식물-화합물 데이터:", len(plant))
print("RDKit feature:", len(rdkit))


# ==================================================
# 2. ChEMBL이 연결된 식물 화합물만 선택
# ==================================================

plant = plant[
    plant["ChEMBL_ID"].notna()
].copy()

print()
print("========================================")
print("식물 화합물")
print("========================================")
print("ChEMBL 연결 행:", len(plant))
print(
    "고유 ChEMBL:",
    plant["ChEMBL_ID"].nunique()
)


# ==================================================
# 3. AI 모델이 사용하는 ChEMBL 목록
# ==================================================

model_chembl = set(
    rdkit["ChEMBL_ID"]
    .dropna()
    .unique()
)

print()
print("========================================")
print("AI 모델 화합물")
print("========================================")
print(
    "AI 모델 ChEMBL:",
    len(model_chembl)
)


# ==================================================
# 4. AI 모델에 존재하는 화합물만 선택
# ==================================================

ready = plant[
    plant["ChEMBL_ID"].isin(model_chembl)
].copy()


# 같은 식물-화합물 관계 중복 제거
ready = ready.drop_duplicates(
    subset=[
        "Plant_ID",
        "ChEMBL_ID"
    ]
).copy()


# ==================================================
# 5. RDKit feature 연결 확인
# ==================================================

rdkit_ids = set(
    rdkit["ChEMBL_ID"]
    .dropna()
    .unique()
)

ready["RDKit_Feature_OK"] = (
    ready["ChEMBL_ID"].isin(rdkit_ids)
)


# ==================================================
# 6. 결과 확인
# ==================================================

print()
print("========================================")
print("AI 예측 준비 결과")
print("========================================")
print(
    "예측 가능한 식물-화합물 관계:",
    len(ready)
)

print(
    "고유 식물:",
    ready["Plant_ID"].nunique()
)

print(
    "고유 ChEMBL:",
    ready["ChEMBL_ID"].nunique()
)

print(
    "RDKit 연결 성공:",
    ready["RDKit_Feature_OK"].sum()
)

print(
    "RDKit 연결 실패:",
    (~ready["RDKit_Feature_OK"]).sum()
)


# ==================================================
# 7. 식물별 AI 예측 가능 화합물
# ==================================================

plant_summary = (
    ready
    .groupby(
        [
            "Plant_ID",
            "Scientific_Name"
        ]
    )
    .agg(
        AI_Predictable_Compounds=(
            "ChEMBL_ID",
            "nunique"
        )
    )
    .reset_index()
)


print()
print("========================================")
print("식물별 AI 예측 가능 화합물")
print("========================================")

print(
    plant_summary.to_string(index=False)
)


# ==================================================
# 8. 저장
# ==================================================

ready.to_csv(
    OUTPUT_FILE,
    index=False,
    encoding="utf-8-sig"
)


print()
print("========================================")
print("AI 예측 준비 데이터 저장 완료")
print("========================================")
print(
    "파일:",
    OUTPUT_FILE
)