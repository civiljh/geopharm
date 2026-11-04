import pandas as pd


ML_FILE = "data/processed/ml_dataset.csv"
PROTEIN_FILE = "data/processed/protein_features.csv"
OUTPUT_FILE = "data/processed/ml_dataset_protein.csv"


# --------------------------------------------------
# 1. 기존 ML 데이터 불러오기
# --------------------------------------------------

ml = pd.read_csv(ML_FILE)

print("ML 데이터:", len(ml))
print("ML 고유 UniProt:", ml["UniProt_ID"].nunique())


# --------------------------------------------------
# 2. 단백질 feature 불러오기
# --------------------------------------------------

protein = pd.read_csv(PROTEIN_FILE)

print("Protein feature:", len(protein))
print("Protein 고유 UniProt:", protein["UniProt_ID"].nunique())


# --------------------------------------------------
# 3. 단백질 feature 연결
# --------------------------------------------------

dataset = ml.merge(
    protein,
    on="UniProt_ID",
    how="left",
    validate="many_to_one"
)


# --------------------------------------------------
# 4. 연결 상태 확인
# --------------------------------------------------

protein_feature_columns = [
    column
    for column in protein.columns
    if column != "UniProt_ID"
]

missing_features = dataset[
    protein_feature_columns
].isna().any(axis=1)


print()
print("===== Protein Feature 연결 결과 =====")
print("전체 ML 행:", len(dataset))
print("Protein feature 수:", len(protein_feature_columns))
print(
    "연결 성공:",
    (~missing_features).sum()
)
print(
    "연결 실패:",
    missing_features.sum()
)


# --------------------------------------------------
# 5. 데이터 크기 확인
# --------------------------------------------------

print()
print("===== 최종 데이터셋 =====")
print("행:", len(dataset))
print("열:", len(dataset.columns))


# --------------------------------------------------
# 6. 저장
# --------------------------------------------------

dataset.to_csv(
    OUTPUT_FILE,
    index=False,
    encoding="utf-8-sig"
)

print()
print("ML + Protein 통합 데이터셋 생성 완료")
print("저장:", OUTPUT_FILE)