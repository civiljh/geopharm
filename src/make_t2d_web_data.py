import pandas as pd
from pathlib import Path


PLANT_FILE = Path(
    "data/processed/t2d_plant_priority_score.csv"
)

TARGET_FILE = Path(
    "data/processed/t2d_target_summary.csv"
)

CANDIDATE_FILE = Path(
    "data/processed/t2d_key_candidates.csv"
)

OUTPUT_FILE = Path(
    "data/processed/t2d_web_data.csv"
)


print("Loading T2D web data...")


# --------------------------------------------------
# 1. Load source files
# --------------------------------------------------

plant_df = pd.read_csv(
    PLANT_FILE
)

target_df = pd.read_csv(
    TARGET_FILE
)

candidate_df = pd.read_csv(
    CANDIDATE_FILE
)


# --------------------------------------------------
# 2. Check required columns
# --------------------------------------------------

plant_required = [
    "Priority_Rank",
    "Plant_ID",
    "Scientific_Name",
    "Compound_Count",
    "Target_Count",
    "Max_pChEMBL",
    "Mean_pChEMBL",
    "Priority_Score",
    "Compound_Evidence_Level",
    "Reliability_Category",
]

target_required = [
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

candidate_required = [
    "Plant_ID",
    "Scientific_Name",
    "Candidate_Rank",
    "Compound_Name",
    "ChEMBL_ID",
    "UniProt_ID",
    "Predicted_pChEMBL",
    "Target_Evidence",
    "Target_Role",
]


missing_plant = [
    col
    for col in plant_required
    if col not in plant_df.columns
]

missing_target = [
    col
    for col in target_required
    if col not in target_df.columns
]

missing_candidate = [
    col
    for col in candidate_required
    if col not in candidate_df.columns
]


if missing_plant:
    raise ValueError(
        f"Missing plant columns: {missing_plant}"
    )

if missing_target:
    raise ValueError(
        f"Missing target columns: {missing_target}"
    )

if missing_candidate:
    raise ValueError(
        f"Missing candidate columns: {missing_candidate}"
    )


# --------------------------------------------------
# 3. Create plant-level web data
# --------------------------------------------------

plant_web = plant_df[
    [
        "Priority_Rank",
        "Plant_ID",
        "Scientific_Name",
        "Compound_Count",
        "Target_Count",
        "Max_pChEMBL",
        "Mean_pChEMBL",
        "Priority_Score",
        "Compound_Evidence_Level",
        "Reliability_Category",
    ]
].copy()


plant_web = plant_web.rename(
    columns={
        "Priority_Rank":
            "Plant_Priority_Rank",
        "Priority_Score":
            "Plant_Priority_Score",
    }
)


# --------------------------------------------------
# 4. Create target-level web data
# --------------------------------------------------

target_web = target_df[
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
].copy()


# --------------------------------------------------
# 5. Create candidate-level web data
# --------------------------------------------------

candidate_web = candidate_df[
    [
        "Plant_ID",
        "Scientific_Name",
        "Candidate_Rank",
        "Compound_Name",
        "ChEMBL_ID",
        "UniProt_ID",
        "Predicted_pChEMBL",
        "Target_Evidence",
        "Target_Role",
    ]
].copy()


# --------------------------------------------------
# 6. Add plant information to candidates
# --------------------------------------------------

candidate_web = candidate_web.merge(
    plant_web[
        [
            "Plant_ID",
            "Plant_Priority_Rank",
            "Plant_Priority_Score",
            "Compound_Evidence_Level",
            "Reliability_Category",
        ]
    ],
    on="Plant_ID",
    how="left",
)


# --------------------------------------------------
# 7. Add target information to candidates
# --------------------------------------------------

candidate_web = candidate_web.merge(
    target_web[
        [
            "UniProt_ID",
            "Target_Rank",
            "Target_Priority_Score",
        ]
    ],
    on="UniProt_ID",
    how="left",
)


# --------------------------------------------------
# 8. Rename candidate rank
# --------------------------------------------------

candidate_web = candidate_web.rename(
    columns={
        "Candidate_Rank":
            "Key_Candidate_Rank",
    }
)


# --------------------------------------------------
# 9. Sort candidate data
# --------------------------------------------------

candidate_web = candidate_web.sort_values(
    [
        "Plant_Priority_Rank",
        "Key_Candidate_Rank",
    ],
    ascending=True,
)


# --------------------------------------------------
# 10. Save plant-level data
# --------------------------------------------------

plant_output = Path(
    "data/processed/t2d_web_plants.csv"
)

plant_web.to_csv(
    plant_output,
    index=False,
    encoding="utf-8-sig",
)


# --------------------------------------------------
# 11. Save target-level data
# --------------------------------------------------

target_output = Path(
    "data/processed/t2d_web_targets.csv"
)

target_web.to_csv(
    target_output,
    index=False,
    encoding="utf-8-sig",
)


# --------------------------------------------------
# 12. Save candidate-level data
# --------------------------------------------------

candidate_output = Path(
    "data/processed/t2d_web_candidates.csv"
)

candidate_web.to_csv(
    candidate_output,
    index=False,
    encoding="utf-8-sig",
)


# --------------------------------------------------
# 13. Create combined file
#
# This file is intended for easy inspection.
# The three dedicated files above are preferred
# for actual web application use.
# --------------------------------------------------

combined = candidate_web.copy()

combined["Analysis_Type"] = (
    "T2D_Key_Candidate"
)

combined.to_csv(
    OUTPUT_FILE,
    index=False,
    encoding="utf-8-sig",
)


# --------------------------------------------------
# 14. Display result
# --------------------------------------------------

print()
print("T2D web data complete.")

print()
print("Plant data:")
print(
    "Output:",
    plant_output
)
print(
    "Rows:",
    len(plant_web)
)

print()
print("Target data:")
print(
    "Output:",
    target_output
)
print(
    "Rows:",
    len(target_web)
)

print()
print("Candidate data:")
print(
    "Output:",
    candidate_output
)
print(
    "Rows:",
    len(candidate_web)
)

print()
print("Combined data:")
print(
    "Output:",
    OUTPUT_FILE
)
print(
    "Rows:",
    len(combined)
)

print()
print("Plants:")
print(
    plant_web[
        [
            "Plant_Priority_Rank",
            "Plant_ID",
            "Scientific_Name",
            "Plant_Priority_Score",
        ]
    ]
    .head(10)
    .to_string(index=False)
)

print()
print("Targets:")
print(
    target_web[
        [
            "Target_Rank",
            "UniProt_ID",
            "Target_Evidence",
            "Target_Role",
            "Target_Priority_Score",
        ]
    ]
    .to_string(index=False)
)

print()
print("Key candidate targets:")
print(
    candidate_web[
        "UniProt_ID"
    ]
    .value_counts()
    .to_string()
)