import pandas as pd
import joblib


# ==================================================
# 파일 설정
# ==================================================

INPUT_FILE = "data/processed/plant_ai_prediction_ready.csv"
RDKIT_FILE = "data/processed/rdkit_features.csv"
PROTEIN_FILE = "data/processed/protein_features.csv"

MODEL_FILE = "data/processed/random_forest_ic50_protein.joblib"

OUTPUT_FILE = "data/processed/plant_ai_predictions.csv"


# ==================================================
# 1. 데이터 불러오기
# ==================================================

plant = pd.read_csv(INPUT_FILE)
rdkit = pd.read_csv(RDKIT_FILE)
protein = pd.read_csv(PROTEIN_FILE)

print("========================================")
print("데이터 불러오기")
print("========================================")
print("식물-화합물 관계:", len(plant))
print("RDKit 화합물:", len(rdkit))
print("Protein:", len(protein))


# ==================================================
# 2. AI 모델 불러오기
# ==================================================

model = joblib.load(MODEL_FILE)

print()
print("========================================")
print("AI 모델")
print("========================================")
print("모델:", MODEL_FILE)


# ==================================================
# 3. 학습 당시 사용한 Morgan Feature 확인
# ==================================================

morgan_columns = [
    column
    for column in rdkit.columns
    if column.startswith("Morgan_")
]

print()
print("========================================")
print("화합물 Feature")
print("========================================")
print("Morgan feature:", len(morgan_columns))


# ==================================================
# 4. Protein Feature
# ==================================================

protein_feature_columns = [
    column
    for column in protein.columns
    if column != "UniProt_ID"
]

print()
print("========================================")
print("Protein Feature")
print("========================================")
print("Protein feature:", len(protein_feature_columns))


# ==================================================
# 5. 최종 Feature
# ==================================================
#
# 학습 당시:
#
# Morgan 2048
# +
# Protein 26
# =
# 2074
#
# RDKit descriptor 9개는 사용하지 않음.
# ==================================================

feature_columns = (
    morgan_columns +
    protein_feature_columns
)

print()
print("========================================")
print("최종 AI Feature")
print("========================================")
print("전체 feature:", len(feature_columns))


# ==================================================
# 6. 모델이 실제 학습한 Feature와 비교
# ==================================================

model_feature_names = list(
    model.feature_names_in_
)

print()
print("========================================")
print("모델 Feature 검증")
print("========================================")
print(
    "모델 학습 Feature:",
    len(model_feature_names)
)

print(
    "현재 예측 Feature:",
    len(feature_columns)
)


if model_feature_names != feature_columns:

    print()
    print("Feature 순서 또는 이름이 다릅니다.")

    missing_from_prediction = [
        column
        for column in model_feature_names
        if column not in feature_columns
    ]

    extra_in_prediction = [
        column
        for column in feature_columns
        if column not in model_feature_names
    ]

    print(
        "예측 데이터에서 빠진 Feature:",
        missing_from_prediction
    )

    print(
        "예측 데이터에 추가된 Feature:",
        extra_in_prediction
    )

    raise SystemExit(
        "모델 Feature와 예측 Feature가 일치하지 않습니다."
    )

print("Feature 검증 성공")


# ==================================================
# 7. 식물 화합물 + RDKit 연결
# ==================================================

plant = plant.merge(
    rdkit[
        ["ChEMBL_ID"] +
        morgan_columns
    ],
    on="ChEMBL_ID",
    how="inner",
    validate="many_to_one"
)

print()
print("========================================")
print("식물 화합물 + Morgan Feature")
print("========================================")
print("연결 후:", len(plant))
print(
    "고유 ChEMBL:",
    plant["ChEMBL_ID"].nunique()
)


# ==================================================
# 8. 식물 화합물 × Protein 조합 생성
# ==================================================

plant["_merge_key"] = 1
protein["_merge_key"] = 1

prediction_input = pd.merge(
    plant,
    protein,
    on="_merge_key",
    how="inner"
)

prediction_input = prediction_input.drop(
    columns=["_merge_key"]
)

print()
print("========================================")
print("AI 예측 조합 생성")
print("========================================")
print(
    "예측 행:",
    len(prediction_input)
)

print(
    "식물:",
    prediction_input["Plant_ID"].nunique()
)

print(
    "화합물:",
    prediction_input["ChEMBL_ID"].nunique()
)

print(
    "Protein:",
    prediction_input["UniProt_ID"].nunique()
)


# ==================================================
# 9. AI 입력 데이터 생성
# ==================================================

X = prediction_input[
    feature_columns
].copy()

print()
print("========================================")
print("AI 입력 데이터")
print("========================================")
print("Feature 수:", len(X.columns))
print("입력 행:", len(X))


# ==================================================
# 10. 결측값 검사
# ==================================================

missing = X.isna().any(axis=1)

print()
print("========================================")
print("결측값 검사")
print("========================================")
print(
    "정상 행:",
    (~missing).sum()
)

print(
    "결측 행:",
    missing.sum()
)


if missing.sum() > 0:

    print()
    print("결측값이 있는 행은 예측에서 제외합니다.")

    prediction_input = prediction_input.loc[
        ~missing
    ].copy()

    X = prediction_input[
        feature_columns
    ].copy()


# ==================================================
# 11. AI 예측
# ==================================================

print()
print("========================================")
print("AI 예측 시작")
print("========================================")

predicted_pchembl = model.predict(X)

print("AI 예측 완료")


# ==================================================
# 12. 결과 정리
# ==================================================

result_columns = [
    "Plant_ID",
    "Scientific_Name",
    "KNApSAcK_ID",
    "Compound_Name",
    "ChEMBL_ID",
    "UniProt_ID"
]

result = prediction_input[
    result_columns
].copy()

result["Predicted_pChEMBL"] = (
    predicted_pchembl
)


# ==================================================
# 13. 예측값 정렬
# ==================================================

result = result.sort_values(
    [
        "Plant_ID",
        "Predicted_pChEMBL"
    ],
    ascending=[
        True,
        False
    ]
).reset_index(drop=True)


# ==================================================
# 14. 결과 확인
# ==================================================

print()
print("========================================")
print("AI 예측 결과 일부")
print("========================================")

print(
    result.head(20).to_string(
        index=False
    )
)


# ==================================================
# 15. 저장
# ==================================================

result.to_csv(
    OUTPUT_FILE,
    index=False,
    encoding="utf-8-sig"
)

print()
print("========================================")
print("AI 예측 저장 완료")
print("========================================")
print(
    "최종 예측 행:",
    len(result)
)

print(
    "파일:",
    OUTPUT_FILE
)