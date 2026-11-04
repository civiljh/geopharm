import pandas as pd

ML_FILE = "data/processed/ml_affinity.csv"
RDKit_FILE = "data/processed/rdkit_features.csv"
OUTPUT_FILE = "data/processed/ml_dataset.csv"

# --------------------------------------------------
# 1. 데이터 불러오기
# --------------------------------------------------

ml = pd.read_csv(ML_FILE)
rdkit = pd.read_csv(RDKit_FILE)

print("ML 데이터:", len(ml))
print("RDKit feature:", len(rdkit))


# --------------------------------------------------
# 2. ChEMBL_ID 기준으로 결합
# --------------------------------------------------

dataset = ml.merge(
    rdkit,
    on="ChEMBL_ID",
    how="left",
    validate="many_to_one"
)


# --------------------------------------------------
# 3. RDKit feature 연결 상태 확인
# --------------------------------------------------

feature_columns = [
    column
    for column in rdkit.columns
    if column != "ChEMBL_ID"
]

missing_features = dataset[feature_columns].isna().any(axis=1)

print()
print("전체 ML 행:", len(dataset))
print("RDKit feature 수:", len(feature_columns))
print("Feature 연결 성공:", (~missing_features).sum())
print("Feature 연결 실패:", missing_features.sum())


# --------------------------------------------------
# 4. 저장
# --------------------------------------------------

dataset.to_csv(
    OUTPUT_FILE,
    index=False,
    encoding="utf-8-sig"
)

print()
print("ML 통합 데이터셋 생성 완료")
print("행:", len(dataset))
print("열:", len(dataset.columns))
print("저장:", OUTPUT_FILE)