import pandas as pd
import numpy as np
from pathlib import Path
from compound_identity import compound_keys


INPUT_FILE = Path(
    "data/processed/t2d_plant_predictions.csv"
)

OUTPUT_FILE = Path(
    "data/processed/t2d_plant_priority_score.csv"
)


print("Loading all T2D plant predictions...")
df = pd.read_csv(INPUT_FILE)
df["Compound_Key"] = compound_keys(df)


# --------------------------------------------------
# 1. Basic validation
# --------------------------------------------------

required_columns = [
    "Plant_ID",
    "Scientific_Name",
    "Compound_Name",
    "ChEMBL_ID",
    "UniProt_ID",
    "Predicted_pChEMBL",
]

missing = [
    col for col in required_columns
    if col not in df.columns
]

if missing:
    raise ValueError(
        f"Missing required columns: {missing}"
    )


# --------------------------------------------------
# 2. Plant-level statistics
#
# 모든 T2D 식물을 대상으로 계산한다.
# 식물 특이적 화합물만 사용하지 않는다.
# --------------------------------------------------

print("Calculating plant-level statistics...")

summary = (
    df.groupby(
        ["Plant_ID", "Scientific_Name"],
        as_index=False,
    )
    .agg(
        Compound_Count=("Compound_Key", "nunique"),
        Target_Count=(
            "UniProt_ID",
            "nunique",
        ),
        Max_pChEMBL=(
            "Predicted_pChEMBL",
            "max",
        ),
        Mean_pChEMBL=(
            "Predicted_pChEMBL",
            "mean",
        ),
        Median_pChEMBL=(
            "Predicted_pChEMBL",
            "median",
        ),
    )
)


# --------------------------------------------------
# 3. Min-Max normalization
# --------------------------------------------------

def min_max_scale(series):
    minimum = series.min()
    maximum = series.max()

    if maximum == minimum:
        return pd.Series(
            [1.0] * len(series),
            index=series.index,
        )

    return (
        (series - minimum)
        / (maximum - minimum)
    )


summary["Max_Score"] = min_max_scale(
    summary["Max_pChEMBL"]
)

summary["Mean_Score"] = min_max_scale(
    summary["Mean_pChEMBL"]
)


# --------------------------------------------------
# 4. Compound evidence score
#
# 화합물 수가 매우 많은 식물이
# 점수를 지나치게 독점하지 않도록 log1p 사용
# --------------------------------------------------

summary["Compound_Log"] = np.log1p(
    summary["Compound_Count"]
)

summary["Compound_Evidence_Score"] = min_max_scale(
    summary["Compound_Log"]
)


# --------------------------------------------------
# 5. Raw priority score
#
# Max prediction       30%
# Mean prediction      40%
# Compound evidence    30%
# --------------------------------------------------

summary["Raw_Priority_Score"] = (
    summary["Max_Score"] * 0.30
    + summary["Mean_Score"] * 0.40
    + summary["Compound_Evidence_Score"] * 0.30
) * 100


# --------------------------------------------------
# 6. Reliability factor
#
# 화합물이 적은 식물은 높은 예측값 하나만으로
# 전체 순위가 올라가는 것을 방지한다.
#
# 공식:
# sqrt(Compound_Count / (Compound_Count + 10))
# --------------------------------------------------

summary["Reliability_Factor"] = np.sqrt(
    summary["Compound_Count"]
    / (summary["Compound_Count"] + 10)
)


# --------------------------------------------------
# 7. Final priority score
# --------------------------------------------------

summary["Priority_Score"] = (
    summary["Raw_Priority_Score"]
    * summary["Reliability_Factor"]
)


# --------------------------------------------------
# 8. Evidence level
# --------------------------------------------------

def evidence_level(count):
    if count >= 30:
        return "High"
    elif count >= 10:
        return "Medium"
    else:
        return "Low"


summary["Compound_Evidence_Level"] = (
    summary["Compound_Count"]
    .apply(evidence_level)
)


# --------------------------------------------------
# 9. Reliability category
# --------------------------------------------------

def reliability_category(count):
    if count >= 30:
        return "High"
    elif count >= 10:
        return "Medium"
    elif count >= 3:
        return "Low"
    else:
        return "Very Low"


summary["Reliability_Category"] = (
    summary["Compound_Count"]
    .apply(reliability_category)
)


# --------------------------------------------------
# 10. Sort
# --------------------------------------------------

summary = summary.sort_values(
    [
        "Priority_Score",
        "Mean_pChEMBL",
        "Max_pChEMBL",
    ],
    ascending=False,
)


# --------------------------------------------------
# 11. Rank
# --------------------------------------------------

summary.insert(
    0,
    "Priority_Rank",
    range(1, len(summary) + 1),
)


# --------------------------------------------------
# 12. Select final columns
# --------------------------------------------------

output_columns = [
    "Priority_Rank",
    "Plant_ID",
    "Scientific_Name",
    "Compound_Count",
    "Target_Count",
    "Max_pChEMBL",
    "Mean_pChEMBL",
    "Median_pChEMBL",
    "Raw_Priority_Score",
    "Reliability_Factor",
    "Priority_Score",
    "Compound_Evidence_Level",
    "Reliability_Category",
]

summary = summary[output_columns]


# --------------------------------------------------
# 13. Save
# --------------------------------------------------

OUTPUT_FILE.parent.mkdir(
    parents=True,
    exist_ok=True,
)

summary.to_csv(
    OUTPUT_FILE,
    index=False,
    encoding="utf-8-sig",
)


# --------------------------------------------------
# 14. Display
# --------------------------------------------------

print()
print("T2D plant priority scoring complete.")

print("Output:", OUTPUT_FILE)
print("Plants:", len(summary))

print()
print("Top 20 T2D plant priorities:")
print(
    summary.head(20).to_string(
        index=False
    )
)
