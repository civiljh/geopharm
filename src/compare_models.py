import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


BASELINE_FILE = "data/processed/random_forest_ic50_predictions.csv"
PROTEIN_FILE = "data/processed/random_forest_ic50_protein_predictions.csv"

OUTPUT_FILE = "data/processed/model_comparison.csv"


# --------------------------------------------------
# 1. 예측 결과 불러오기
# --------------------------------------------------

baseline = pd.read_csv(BASELINE_FILE)
protein = pd.read_csv(PROTEIN_FILE)

print("Compound-only 예측:", len(baseline))
print("Compound + Protein 예측:", len(protein))


# --------------------------------------------------
# 2. 실제값과 예측값 준비
# --------------------------------------------------

y_true_baseline = baseline["pChEMBL"]
y_pred_baseline = baseline["Predicted_pChEMBL"]

y_true_protein = protein["pChEMBL"]
y_pred_protein = protein["Predicted_pChEMBL"]


# --------------------------------------------------
# 3. 성능 계산
# --------------------------------------------------

baseline_mae = mean_absolute_error(
    y_true_baseline,
    y_pred_baseline
)

baseline_rmse = mean_squared_error(
    y_true_baseline,
    y_pred_baseline
) ** 0.5

baseline_r2 = r2_score(
    y_true_baseline,
    y_pred_baseline
)


protein_mae = mean_absolute_error(
    y_true_protein,
    y_pred_protein
)

protein_rmse = mean_squared_error(
    y_true_protein,
    y_pred_protein
) ** 0.5

protein_r2 = r2_score(
    y_true_protein,
    y_pred_protein
)


# --------------------------------------------------
# 4. Feature 수
# --------------------------------------------------

baseline_feature_count = 2048
protein_feature_count = 2074


# --------------------------------------------------
# 5. 모델 비교표 생성
# --------------------------------------------------

comparison = pd.DataFrame([
    {
        "Model": "Compound-only",
        "Feature_Count": baseline_feature_count,
        "MAE": baseline_mae,
        "RMSE": baseline_rmse,
        "R2": baseline_r2
    },
    {
        "Model": "Compound + Protein",
        "Feature_Count": protein_feature_count,
        "MAE": protein_mae,
        "RMSE": protein_rmse,
        "R2": protein_r2
    }
])


# --------------------------------------------------
# 6. 변화량 계산
# --------------------------------------------------

mae_change = protein_mae - baseline_mae
rmse_change = protein_rmse - baseline_rmse
r2_change = protein_r2 - baseline_r2


# --------------------------------------------------
# 7. 개선율 계산
# --------------------------------------------------

mae_improvement = (
    (baseline_mae - protein_mae)
    / baseline_mae
    * 100
)

rmse_improvement = (
    (baseline_rmse - protein_rmse)
    / baseline_rmse
    * 100
)

r2_improvement = (
    (protein_r2 - baseline_r2)
    / abs(baseline_r2)
    * 100
)


# --------------------------------------------------
# 8. 비교 결과 출력
# --------------------------------------------------

print()
print("========================================")
print("        모델 성능 비교")
print("========================================")

print(
    comparison.to_string(
        index=False,
        float_format=lambda x: f"{x:.4f}"
    )
)


print()
print("========================================")
print("        모델 변화량")
print("========================================")

print(f"MAE 변화량 : {mae_change:.4f}")
print(f"RMSE 변화량: {rmse_change:.4f}")
print(f"R² 변화량  : {r2_change:.4f}")


print()
print("========================================")
print("        개선율")
print("========================================")

print(f"MAE 개선율 : {mae_improvement:.2f}%")
print(f"RMSE 개선율: {rmse_improvement:.2f}%")
print(f"R² 변화율  : {r2_improvement:.2f}%")


# --------------------------------------------------
# 9. 비교표에 변화량 정보 추가
# --------------------------------------------------

comparison["MAE_Change_vs_Baseline"] = [
    0,
    mae_change
]

comparison["RMSE_Change_vs_Baseline"] = [
    0,
    rmse_change
]

comparison["R2_Change_vs_Baseline"] = [
    0,
    r2_change
]

comparison["MAE_Improvement_Percent"] = [
    0,
    mae_improvement
]

comparison["RMSE_Improvement_Percent"] = [
    0,
    rmse_improvement
]

comparison["R2_Change_Percent"] = [
    0,
    r2_improvement
]


# --------------------------------------------------
# 10. CSV 저장
# --------------------------------------------------

comparison.to_csv(
    OUTPUT_FILE,
    index=False,
    encoding="utf-8-sig"
)


print()
print("========================================")
print("비교표 저장 완료")
print("========================================")
print("저장 위치:", OUTPUT_FILE)