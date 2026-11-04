import pandas as pd
from pathlib import Path


INPUT_FILE = Path(
    "data/processed/t2d_plant_specific_predictions.csv"
)

OUTPUT_FILE = Path(
    "data/processed/t2d_key_candidates.csv"
)


print("Loading T2D plant-specific predictions...")
df = pd.read_csv(INPUT_FILE)


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
# 2. Sort all predictions by strength
# --------------------------------------------------

print()
print("Creating plant-specific key prediction candidates...")

all_sorted = df.sort_values(
    [
        "Plant_ID",
        "Predicted_pChEMBL",
    ],
    ascending=[
        True,
        False,
    ],
).copy()


# --------------------------------------------------
# 3. For each plant + compound,
#    keep the strongest target
# --------------------------------------------------

all_compound = (
    all_sorted
    .drop_duplicates(
        subset=[
            "Plant_ID",
            "ChEMBL_ID",
        ],
        keep="first",
    )
)


# --------------------------------------------------
# 4. Select candidates for every plant
#
# Strong candidates (pChEMBL >= 6) are preferred.
# If a plant has fewer than 10 strong candidates,
# fill the remaining slots with that plant's strongest
# available predictions. This guarantees that every
# plant can appear in the web candidate data.
# --------------------------------------------------

strong = all_compound[
    all_compound["Predicted_pChEMBL"] >= 6.0
].copy()

strong = (
    strong
    .groupby(
        [
            "Plant_ID",
            "Scientific_Name",
        ],
        group_keys=False,
    )
    .head(10)
)

selected_parts = []

for (plant_id, scientific_name), plant_df in all_compound.groupby(
    ["Plant_ID", "Scientific_Name"], sort=True
):
    plant_strong = strong[
        (strong["Plant_ID"] == plant_id)
        & (strong["Scientific_Name"] == scientific_name)
    ]

    selected_ids = set(plant_strong["ChEMBL_ID"])

    fallback = plant_df[
        ~plant_df["ChEMBL_ID"].isin(selected_ids)
    ].head(10 - len(plant_strong))

    selected = pd.concat(
        [plant_strong, fallback],
        ignore_index=True,
    )

    selected_parts.append(selected)

top_candidates = pd.concat(
    selected_parts,
    ignore_index=True,
)


# --------------------------------------------------
# 6. Add candidate rank within plant
# --------------------------------------------------

top_candidates["Candidate_Rank"] = (
    top_candidates
    .groupby("Plant_ID")
    ["Predicted_pChEMBL"]
    .rank(
        method="first",
        ascending=False,
    )
    .astype(int)
)


# --------------------------------------------------
# 7. Reorder columns
# --------------------------------------------------

output_columns = [
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

top_candidates = top_candidates[
    output_columns
]


# --------------------------------------------------
# 8. Sort final output
# --------------------------------------------------

top_candidates = top_candidates.sort_values(
    [
        "Plant_ID",
        "Candidate_Rank",
    ],
    ascending=True,
)


# --------------------------------------------------
# 9. Save
# --------------------------------------------------

OUTPUT_FILE.parent.mkdir(
    parents=True,
    exist_ok=True,
)

top_candidates.to_csv(
    OUTPUT_FILE,
    index=False,
    encoding="utf-8-sig",
)


# --------------------------------------------------
# 10. Display
# --------------------------------------------------

print()
print("T2D key candidate analysis complete.")

print("Output:", OUTPUT_FILE)

print(
    "Plants:",
    top_candidates["Plant_ID"].nunique()
)

print(
    "Candidate rows:",
    len(top_candidates)
)

print()
print("Top candidates:")

print(
    top_candidates[
        [
            "Plant_ID",
            "Scientific_Name",
            "Candidate_Rank",
            "Compound_Name",
            "UniProt_ID",
            "Predicted_pChEMBL",
        ]
    ]
    .head(50)
    .to_string(index=False)
)