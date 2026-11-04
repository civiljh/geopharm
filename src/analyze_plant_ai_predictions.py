import pandas as pd

INPUT_FILE = "data/processed/plant_ai_predictions.csv"

OUTPUT_SUMMARY = "data/processed/plant_ai_prediction_summary.csv"
OUTPUT_TOP = "data/processed/plant_ai_top_candidates.csv"

df = pd.read_csv(INPUT_FILE)

print("========================================")
print("AI 예측 데이터 불러오기")
print("========================================")
print("전체 예측 행:", len(df))
print("식물:", df["Plant_ID"].nunique())
print("화합물:", df["ChEMBL_ID"].nunique())
print("Protein:", df["UniProt_ID"].nunique())


# --------------------------------------------------
# 1. 식물 + 화합물 + 단백질별 최고 예측값
# --------------------------------------------------

summary = (
    df.groupby(
        [
            "Plant_ID",
            "Scientific_Name",
            "ChEMBL_ID",
            "Compound_Name",
            "UniProt_ID"
        ],
        as_index=False
    )
    .agg(
        Predicted_pChEMBL=(
            "Predicted_pChEMBL",
            "max"
        )
    )
)

print()
print("========================================")
print("식물-화합물-단백질별 정리")
print("========================================")
print("정리 후 행:", len(summary))


# --------------------------------------------------
# 2. 식물 + 화합물별 최고 표적 예측
# --------------------------------------------------

compound_best = (
    summary
    .sort_values(
        [
            "Plant_ID",
            "Predicted_pChEMBL"
        ],
        ascending=[
            True,
            False
        ]
    )
    .groupby(
        [
            "Plant_ID",
            "Scientific_Name",
            "ChEMBL_ID",
            "Compound_Name"
        ],
        as_index=False
    )
    .first()
)

print()
print("========================================")
print("식물-화합물별 최고 표적")
print("========================================")
print(
    "식물-화합물 후보:",
    len(compound_best)
)


# --------------------------------------------------
# 3. 식물별 상위 후보
# --------------------------------------------------

top_candidates = (
    compound_best
    .sort_values(
        [
            "Plant_ID",
            "Predicted_pChEMBL"
        ],
        ascending=[
            True,
            False
        ]
    )
    .groupby(
        "Plant_ID",
        group_keys=False
    )
    .head(20)
    .reset_index(drop=True)
)

print()
print("========================================")
print("식물별 상위 AI 후보")
print("========================================")

print(
    top_candidates[
        [
            "Plant_ID",
            "Scientific_Name",
            "Compound_Name",
            "ChEMBL_ID",
            "UniProt_ID",
            "Predicted_pChEMBL"
        ]
    ].to_string(index=False)
)


# --------------------------------------------------
# 4. 식물별 통계
# --------------------------------------------------

plant_summary = (
    compound_best
    .groupby(
        [
            "Plant_ID",
            "Scientific_Name"
        ],
        as_index=False
    )
    .agg(
        AI_Predictable_Compounds=(
            "ChEMBL_ID",
            "nunique"
        ),
        Max_Predicted_pChEMBL=(
            "Predicted_pChEMBL",
            "max"
        ),
        Mean_Predicted_pChEMBL=(
            "Predicted_pChEMBL",
            "mean"
        )
    )
    .sort_values(
        "Max_Predicted_pChEMBL",
        ascending=False
    )
)

print()
print("========================================")
print("식물별 AI 예측 통계")
print("========================================")

print(
    plant_summary.to_string(index=False)
)


# --------------------------------------------------
# 5. 파일 저장
# --------------------------------------------------

summary.to_csv(
    OUTPUT_SUMMARY,
    index=False,
    encoding="utf-8-sig"
)

top_candidates.to_csv(
    OUTPUT_TOP,
    index=False,
    encoding="utf-8-sig"
)

print()
print("========================================")
print("AI 예측 분석 저장 완료")
print("========================================")
print(
    "전체 정리 파일:",
    OUTPUT_SUMMARY
)

print(
    "상위 후보 파일:",
    OUTPUT_TOP
)