import pandas as pd
import joblib

from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


TRAIN_FILE = "data/processed/ic50_train.csv"
TEST_FILE = "data/processed/ic50_test.csv"

MODEL_FILE = "data/processed/random_forest_ic50.joblib"
PREDICTION_FILE = "data/processed/random_forest_ic50_predictions.csv"


# --------------------------------------------------
# 1. 데이터 불러오기
# --------------------------------------------------

train = pd.read_csv(TRAIN_FILE)
test = pd.read_csv(TEST_FILE)

print("Train:", len(train))
print("Test:", len(test))


# --------------------------------------------------
# 2. Morgan fingerprint 선택
# --------------------------------------------------

feature_columns = [
    column
    for column in train.columns
    if column.startswith("Morgan_")
]

print("Morgan feature 수:", len(feature_columns))


# --------------------------------------------------
# 3. 입력 X / 정답 y 구성
# --------------------------------------------------

X_train = train[feature_columns]
y_train = train["pChEMBL"]

X_test = test[feature_columns]
y_test = test["pChEMBL"]


# --------------------------------------------------
# 4. Random Forest 모델
# --------------------------------------------------

model = RandomForestRegressor(
    n_estimators=300,
    random_state=42,
    n_jobs=-1,
    max_features="sqrt"
)


# --------------------------------------------------
# 5. 모델 학습
# --------------------------------------------------

print()
print("Random Forest 학습 시작...")

model.fit(X_train, y_train)

print("학습 완료")


# --------------------------------------------------
# 6. Test 데이터 예측
# --------------------------------------------------

pred = model.predict(X_test)


# --------------------------------------------------
# 7. 성능 평가
# --------------------------------------------------

mae = mean_absolute_error(y_test, pred)
rmse = mean_squared_error(y_test, pred) ** 0.5
r2 = r2_score(y_test, pred)

print()
print("===== Random Forest 성능 =====")
print("MAE :", mae)
print("RMSE:", rmse)
print("R²  :", r2)


# --------------------------------------------------
# 8. 예측 결과 저장
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
# 9. 학습된 모델 저장
# --------------------------------------------------

joblib.dump(
    model,
    MODEL_FILE
)


# --------------------------------------------------
# 10. 결과 출력
# --------------------------------------------------

print()
print("===== 예측 결과 일부 =====")
print(
    result.head(10).to_string(index=False)
)

print()
print("모델 저장 완료:", MODEL_FILE)
print("예측 결과 저장 완료:", PREDICTION_FILE)