import pandas as pd
import joblib

from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


TRAIN_FILE = "data/processed/ic50_protein_train.csv"
TEST_FILE = "data/processed/ic50_protein_test.csv"

MODEL_FILE = "data/processed/random_forest_ic50_protein.joblib"
PREDICTION_FILE = "data/processed/random_forest_ic50_protein_predictions.csv"


# --------------------------------------------------
# 1. 데이터 불러오기
# --------------------------------------------------

train = pd.read_csv(TRAIN_FILE)
test = pd.read_csv(TEST_FILE)

print("Train:", len(train))
print("Test:", len(test))


# --------------------------------------------------
# 2. 화합물 feature 선택
# --------------------------------------------------

morgan_columns = [
    column
    for column in train.columns
    if column.startswith("Morgan_")
]


# --------------------------------------------------
# 3. 단백질 feature 선택
# --------------------------------------------------

protein_columns = [
    column
    for column in train.columns
    if column in [
        "Sequence_Length",
        "AA_A",
        "AA_C",
        "AA_D",
        "AA_E",
        "AA_F",
        "AA_G",
        "AA_H",
        "AA_I",
        "AA_K",
        "AA_L",
        "AA_M",
        "AA_N",
        "AA_P",
        "AA_Q",
        "AA_R",
        "AA_S",
        "AA_T",
        "AA_V",
        "AA_W",
        "AA_Y",
        "Hydrophobic_Fraction",
        "Aromatic_Fraction",
        "Positive_Fraction",
        "Negative_Fraction",
        "Polar_Fraction"
    ]
]


feature_columns = morgan_columns + protein_columns


print()
print("Morgan feature 수:", len(morgan_columns))
print("Protein feature 수:", len(protein_columns))
print("전체 feature 수:", len(feature_columns))


# --------------------------------------------------
# 4. 입력 X / 정답 y 구성
# --------------------------------------------------

X_train = train[feature_columns]
y_train = train["pChEMBL"]

X_test = test[feature_columns]
y_test = test["pChEMBL"]


# --------------------------------------------------
# 5. Random Forest 모델
# --------------------------------------------------

model = RandomForestRegressor(
    n_estimators=300,
    random_state=42,
    n_jobs=-1,
    max_features="sqrt"
)


# --------------------------------------------------
# 6. 모델 학습
# --------------------------------------------------

print()
print("Random Forest Protein 모델 학습 시작...")

model.fit(X_train, y_train)

print("학습 완료")


# --------------------------------------------------
# 7. Test 데이터 예측
# --------------------------------------------------

pred = model.predict(X_test)


# --------------------------------------------------
# 8. 성능 평가
# --------------------------------------------------

mae = mean_absolute_error(y_test, pred)
rmse = mean_squared_error(y_test, pred) ** 0.5
r2 = r2_score(y_test, pred)


print()
print("===== Random Forest + Protein 성능 =====")
print("MAE :", mae)
print("RMSE:", rmse)
print("R²  :", r2)


# --------------------------------------------------
# 9. 예측 결과 저장
# --------------------------------------------------

result = test[
    [
        "ChEMBL_ID",
        "UniProt_ID",
        "pChEMBL"
    ]
].copy()

result["Predicted_pChEMBL"] = pred

result["Absolute_Error"] = (
    result["pChEMBL"] - result["Predicted_pChEMBL"]
).abs()


result.to_csv(
    PREDICTION_FILE,
    index=False,
    encoding="utf-8-sig"
)


# --------------------------------------------------
# 10. 모델 저장
# --------------------------------------------------

joblib.dump(
    model,
    MODEL_FILE
)


# --------------------------------------------------
# 11. 예측 결과 일부 출력
# --------------------------------------------------

print()
print("===== 예측 결과 일부 =====")
print(
    result.head(10).to_string(index=False)
)


print()
print("모델 저장 완료:", MODEL_FILE)
print("예측 결과 저장 완료:", PREDICTION_FILE)