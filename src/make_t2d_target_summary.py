import pandas as pd
from pathlib import Path
from compound_identity import compound_keys


INPUT_FILE = Path(
    "data/processed/t2d_plant_specific_predictions.csv"
)

OUTPUT_FILE = Path(
    "data/processed/t2d_target_summary.csv"
)


print("Loading T2D plant-specific predictions...")
df = pd.read_csv(INPUT_FILE)
df["Compound_Key"] = compound_keys(df)


# --------------------------------------------------
# 1. Required columns
# --------------------------------------------------

required_columns = [
    "Plant_ID",
    "Scientific_Name",
    "Compound_Name",
    "ChEMBL_ID",
    "UniProt_ID",
    "Predicted_pChEMBL",
    "Target_Evidence",
    "Target_Role",
]

missing = [
    col
    for col in required_columns
    if col not in df.columns
]

if missing:
    raise ValueError(
        f"Missing required columns: {missing}"
    )


# --------------------------------------------------
# 2. Target-level summary
# --------------------------------------------------

print()
print("Calculating target-level statistics...")


summary = (
    df.groupby(
        [
            "UniProt_ID",
            "Target_Evidence",
            "Target_Role",
        ],
        as_index=False,
    )
    .agg(
        Plant_Count=(
            "Plant_ID",
            "nunique",
        ),
        Compound_Count=("Compound_Key", "nunique"),
        Prediction_Count=(
            "Predicted_pChEMBL",
            "count",
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
# 3. Strong prediction count
#
# pChEMBL >= 6
# --------------------------------------------------

strong_counts = (
    df.assign(
        Strong_Prediction=
        df["Predicted_pChEMBL"] >= 6.0
    )
    .groupby("UniProt_ID")
    ["Strong_Prediction"]
    .sum()
    .reset_index(
        name="Strong_Prediction_Count"
    )
)


summary = summary.merge(
    strong_counts,
    on="UniProt_ID",
    how="left",
)


# --------------------------------------------------
# 4. Very strong prediction count
#
# pChEMBL >= 7
# --------------------------------------------------

very_strong_counts = (
    df.assign(
        Very_Strong_Prediction=
        df["Predicted_pChEMBL"] >= 7.0
    )
    .groupby("UniProt_ID")
    ["Very_Strong_Prediction"]
    .sum()
    .reset_index(
        name="Very_Strong_Prediction_Count"
    )
)


summary = summary.merge(
    very_strong_counts,
    on="UniProt_ID",
    how="left",
)


# --------------------------------------------------
# 5. Target priority score
#
# Mean prediction       40%
# Maximum prediction    30%
# Strong predictions    20%
# Plant coverage        10%
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


summary["Mean_Score"] = min_max_scale(
    summary["Mean_pChEMBL"]
)

summary["Max_Score"] = min_max_scale(
    summary["Max_pChEMBL"]
)

summary["Strong_Score"] = min_max_scale(
    summary["Strong_Prediction_Count"]
)

summary["Plant_Coverage_Score"] = min_max_scale(
    summary["Plant_Count"]
)


summary["Target_Priority_Score"] = (
    summary["Mean_Score"] * 0.40
    + summary["Max_Score"] * 0.30
    + summary["Strong_Score"] * 0.20
    + summary["Plant_Coverage_Score"] * 0.10
) * 100


# --------------------------------------------------
# 6. Rank
# --------------------------------------------------

summary = summary.sort_values(
    [
        "Target_Priority_Score",
        "Mean_pChEMBL",
        "Max_pChEMBL",
    ],
    ascending=False,
)


summary.insert(
    0,
    "Target_Rank",
    range(1, len(summary) + 1),
)


# --------------------------------------------------
# 7. Save
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
# 8. Display
# --------------------------------------------------

print()
print("T2D target summary complete.")

print("Output:", OUTPUT_FILE)
print("Targets:", len(summary))

print()
print("T2D target ranking:")

print(
    summary[
        [
            "Target_Rank",
            "UniProt_ID",
            "Target_Evidence",
            "Target_Role",
            "Plant_Count",
            "Compound_Count",
            "Max_pChEMBL",
            "Mean_pChEMBL",
            "Strong_Prediction_Count",
            "Very_Strong_Prediction_Count",
            "Target_Priority_Score",
        ]
    ].to_string(index=False)
)
