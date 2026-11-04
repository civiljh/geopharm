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
    "data/processed/t2d_analysis_data.csv"
)


print("Loading T2D analysis data...")


# --------------------------------------------------
# 1. Load files
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
# 2. Required columns
# --------------------------------------------------

plant_required = [
    "Plant_ID",
    "Scientific_Name",
    "Priority_Score",
    "Compound_Evidence_Level",
    "Reliability_Category",
]

target_required = [
    "UniProt_ID",
    "Target_Evidence",
    "Target_Role",
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
# 3. Select plant information
# --------------------------------------------------

plant_info = plant_df[
    [
        "Plant_ID",
        "Scientific_Name",
        "Priority_Score",
        "Compound_Evidence_Level",
        "Reliability_Category",
    ]
].copy()


# --------------------------------------------------
# 4. Rename plant evidence fields
# --------------------------------------------------

plant_info = plant_info.rename(
    columns={
        "Compound_Evidence_Level":
            "Plant_Evidence_Level",
        "Reliability_Category":
            "Plant_Reliability",
    }
)


# --------------------------------------------------
# 5. Select target information
# --------------------------------------------------

target_info = target_df[
    [
        "UniProt_ID",
        "Target_Evidence",
        "Target_Role",
        "Target_Priority_Score",
    ]
].copy()


# --------------------------------------------------
# 6. Select candidate information
# --------------------------------------------------

candidate_info = candidate_df[
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
# 7. Add target priority
# --------------------------------------------------

candidate_info = candidate_info.merge(
    target_info[
        [
            "UniProt_ID",
            "Target_Priority_Score",
        ]
    ],
    on="UniProt_ID",
    how="left",
)


# --------------------------------------------------
# 8. Add plant priority
# --------------------------------------------------

candidate_info = candidate_info.merge(
    plant_info[
        [
            "Plant_ID",
            "Priority_Score",
            "Plant_Evidence_Level",
            "Plant_Reliability",
        ]
    ],
    on="Plant_ID",
    how="left",
)


# --------------------------------------------------
# 9. Rename plant score
# --------------------------------------------------

candidate_info = candidate_info.rename(
    columns={
        "Priority_Score":
            "Plant_Priority_Score",
    }
)


# --------------------------------------------------
# 10. Calculate combined candidate score
#
# Compound prediction: 60%
# Target priority:     20%
# Plant priority:      20%
# --------------------------------------------------

candidate_info[
    "Candidate_Combined_Score"
] = (
    candidate_info["Predicted_pChEMBL"] * 0.60
    + (
        candidate_info["Target_Priority_Score"]
        / 100
        * 10
        * 0.20
    )
    + (
        candidate_info["Plant_Priority_Score"]
        / 100
        * 10
        * 0.20
    )
)


# --------------------------------------------------
# 11. Sort
# --------------------------------------------------

candidate_info = candidate_info.sort_values(
    [
        "Plant_Priority_Score",
        "Candidate_Combined_Score",
        "Predicted_pChEMBL",
    ],
    ascending=False,
)


# --------------------------------------------------
# 12. Recalculate candidate rank
# --------------------------------------------------

candidate_info[
    "Plant_Candidate_Rank"
] = (
    candidate_info
    .groupby("Plant_ID")
    ["Candidate_Combined_Score"]
    .rank(
        method="first",
        ascending=False,
    )
    .astype(int)
)


candidate_info = candidate_info.sort_values(
    [
        "Plant_Priority_Score",
        "Plant_Candidate_Rank",
    ]
)


# --------------------------------------------------
# 13. Save
# --------------------------------------------------

OUTPUT_FILE.parent.mkdir(
    parents=True,
    exist_ok=True,
)


candidate_info.to_csv(
    OUTPUT_FILE,
    index=False,
    encoding="utf-8-sig",
)


# --------------------------------------------------
# 14. Display result
# --------------------------------------------------

print()
print("T2D analysis data complete.")

print(
    "Output:",
    OUTPUT_FILE
)

print(
    "Rows:",
    len(candidate_info)
)

print(
    "Plants:",
    candidate_info["Plant_ID"].nunique()
)

print(
    "Compounds:",
    candidate_info["ChEMBL_ID"].nunique()
)

print(
    "Targets:",
    candidate_info["UniProt_ID"].nunique()
)


print()
print("Top T2D analysis candidates:")

print(
    candidate_info[
        [
            "Plant_ID",
            "Scientific_Name",
            "Plant_Candidate_Rank",
            "Compound_Name",
            "ChEMBL_ID",
            "UniProt_ID",
            "Predicted_pChEMBL",
            "Target_Priority_Score",
            "Plant_Priority_Score",
            "Candidate_Combined_Score",
        ]
    ]
    .head(20)
    .to_string(index=False)
)