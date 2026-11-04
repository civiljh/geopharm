import pandas as pd
import matplotlib.pyplot as plt

from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


BASELINE_FILE = "data/processed/random_forest_ic50_predictions.csv"
PROTEIN_FILE = "data/processed/random_forest_ic50_protein_predictions.csv"

BASELINE_OUTPUT = "data/processed/compound_only_prediction_plot.png"
PROTEIN_OUTPUT = "data/processed/compound_protein_prediction_plot.png"


# --------------------------------------------------
# 1. 데이터 불러오기
# --------------------------------------------------

baseline = pd.read_csv(BASELINE_FILE)
protein = pd.read_csv(PROTEIN_FILE)

print("Compound-only 예측:", len(baseline))
print("Compound + Protein 예측:", len(protein))


# --------------------------------------------------
# 2. 그래프 생성 함수
# --------------------------------------------------

def make_plot(
    df,
    title,
    output_file
):
    actual = df["pChEMBL"]
    predicted = df["Predicted_pChEMBL"]

    mae = mean_absolute_error(
        actual,
        predicted
    )

    rmse = mean_squared_error(
        actual,
        predicted
    ) ** 0.5

    r2 = r2_score(
        actual,
        predicted
    )

    # 실제값과 예측값의 전체 범위를 사용
    minimum = min(
        actual.min(),
        predicted.min()
    )

    maximum = max(
        actual.max(),
        predicted.max()
    )

    margin = (maximum - minimum) * 0.05

    minimum -= margin
    maximum += margin

    plt.figure(figsize=(8, 8))

    # 실제값 vs 예측값
    plt.scatter(
        actual,
        predicted,
        alpha=0.7
    )

    # 이상적인 예측선
    plt.plot(
        [minimum, maximum],
        [minimum, maximum],
        linestyle="--"
    )

    plt.xlabel("Actual pChEMBL")
    plt.ylabel("Predicted pChEMBL")
    plt.title(title)

    plt.xlim(
        minimum,
        maximum
    )

    plt.ylim(
        minimum,
        maximum
    )

    # 성능 지표 표시
    text = (
        f"MAE = {mae:.4f}\n"
        f"RMSE = {rmse:.4f}\n"
        f"R² = {r2:.4f}"
    )

    plt.text(
        0.05,
        0.95,
        text,
        transform=plt.gca().transAxes,
        verticalalignment="top"
    )

    plt.grid(
        True,
        alpha=0.3
    )

    plt.tight_layout()

    plt.savefig(
        output_file,
        dpi=300
    )

    plt.close()

    print()
    print("그래프 저장 완료:", output_file)


# --------------------------------------------------
# 3. Compound-only 그래프
# --------------------------------------------------

make_plot(
    baseline,
    "Compound-only Random Forest",
    BASELINE_OUTPUT
)


# --------------------------------------------------
# 4. Compound + Protein 그래프
# --------------------------------------------------

make_plot(
    protein,
    "Compound + Protein Random Forest",
    PROTEIN_OUTPUT
)


# --------------------------------------------------
# 5. 완료
# --------------------------------------------------

print()
print("========================================")
print("예측 그래프 생성 완료")
print("========================================")