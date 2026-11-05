import pandas as pd
from pathlib import Path
from compound_identity import compound_keys


# ============================================================
# GeoPharm - 자동 T2D 식물 분석
#
# 역할:
# 1. 전체 AI 예측 데이터를 읽는다.
# 2. T2D 관련 예측 데이터에서 식물별 분석을 수행한다.
# 3. 각 화합물이 몇 개 식물에 존재하는지 계산한다.
# 4. 특정 식물에서만 발견되는 화합물을 구분한다.
# 5. 새로운 식물이 추가되어도 자동으로 분석한다.
#
# 특정 Plant_ID를 코드에 직접 지정하지 않는다.
# ============================================================


PREDICTION_FILE = Path(
    "data/processed/t2d_plant_predictions.csv"
)

PLANT_DATA_FILE = Path(
    "data/processed/plant_ai_predictions.csv"
)

OUTPUT_SUMMARY = Path(
    "data/processed/t2d_plant_summary.csv"
)

OUTPUT_SPECIFIC = Path(
    "data/processed/t2d_plant_specific_predictions.csv"
)

OUTPUT_TOP = Path(
    "data/processed/t2d_top_candidates.csv"
)


print("=" * 70)
print("GeoPharm - 자동 T2D 식물 분석")
print("=" * 70)


# ============================================================
# 1. T2D 예측 데이터 읽기
# ============================================================

print()
print("[1] T2D 예측 데이터 불러오기")

t2d = pd.read_csv(
    PREDICTION_FILE,
    low_memory=False
)

print(f"T2D 예측 행: {len(t2d):,}")
print(f"T2D 식물 수: {t2d['Plant_ID'].nunique()}")


# ============================================================
# 2. 전체 AI 식물 데이터 읽기
# ============================================================

print()
print("[2] 전체 식물 AI 데이터 불러오기")

plant_data = pd.read_csv(
    PLANT_DATA_FILE,
    low_memory=False
)
t2d["Compound_Key"] = compound_keys(t2d)
plant_data["Compound_Key"] = compound_keys(plant_data)

print(f"전체 AI 행: {len(plant_data):,}")
print(f"전체 식물 수: {plant_data['Plant_ID'].nunique()}")


# ============================================================
# 3. 화합물이 몇 개 식물에 존재하는지 계산
# ============================================================

print()
print("[3] 화합물별 식물 수 계산")


compound_plant_count = (
    plant_data
    .loc[lambda frame: frame["Compound_Key"] != ""]
    .groupby("Compound_Key")["Plant_ID"]
    .nunique()
    .reset_index(name="Plant_Count")
)


t2d = t2d.merge(
    compound_plant_count,
    on="Compound_Key",
    how="left"
)


t2d["Plant_Count"] = (
    t2d["Plant_Count"]
    .fillna(0)
    .astype(int)
)


# 현재 데이터에서 한 식물에만 존재하는 화합물
t2d["Plant_Specific"] = (
    t2d["Plant_Count"] == 1
)


print(
    f"화합물 종류: "
    f"{compound_plant_count['Compound_Key'].nunique():,}"
)


# ============================================================
# 4. 전체 식물별 T2D 요약
# ============================================================

print()
print("[4] 식물별 전체 T2D 요약 생성")


summary = (
    t2d
    .groupby(
        ["Plant_ID", "Scientific_Name"],
        as_index=False
    )
    .agg(
        T2D_Compound_Count=("Compound_Key", "nunique"),
        T2D_Target_Count=(
            "UniProt_ID",
            "nunique"
        ),
        Max_Predicted_pChEMBL=(
            "Predicted_pChEMBL",
            "max"
        ),
        Mean_Predicted_pChEMBL=(
            "Predicted_pChEMBL",
            "mean"
        ),
        Median_Predicted_pChEMBL=(
            "Predicted_pChEMBL",
            "median"
        ),
    )
)


summary = summary.sort_values(
    "Max_Predicted_pChEMBL",
    ascending=False
)


OUTPUT_SUMMARY.parent.mkdir(
    parents=True,
    exist_ok=True
)


summary.to_csv(
    OUTPUT_SUMMARY,
    index=False,
    encoding="utf-8-sig"
)


# ============================================================
# 5. 식물 특이적 화합물 추출
# ============================================================

print()
print("[5] 식물 특이적 화합물 분석")


specific = t2d[
    t2d["Plant_Specific"]
].copy()


specific = specific.sort_values(
    "Predicted_pChEMBL",
    ascending=False
)


specific.to_csv(
    OUTPUT_SPECIFIC,
    index=False,
    encoding="utf-8-sig"
)


# ============================================================
# 6. 식물 특이적 화합물 기준 식물 요약
# ============================================================

print()
print("[6] 식물 특이적 화합물 기준 요약")


if len(specific) > 0:

    specific_summary = (
        specific
        .groupby(
            ["Plant_ID", "Scientific_Name"],
            as_index=False
        )
        .agg(
            Plant_Specific_Compound_Count=("Compound_Key", "nunique"),
            Plant_Specific_Target_Count=(
                "UniProt_ID",
                "nunique"
            ),
            Plant_Specific_Max_pChEMBL=(
                "Predicted_pChEMBL",
                "max"
            ),
            Plant_Specific_Mean_pChEMBL=(
                "Predicted_pChEMBL",
                "mean"
            ),
            Plant_Specific_Median_pChEMBL=(
                "Predicted_pChEMBL",
                "median"
            ),
        )
    )

    specific_summary = specific_summary.sort_values(
        "Plant_Specific_Max_pChEMBL",
        ascending=False
    )

else:

    specific_summary = pd.DataFrame(
        columns=[
            "Plant_ID",
            "Scientific_Name",
            "Plant_Specific_Compound_Count",
            "Plant_Specific_Target_Count",
            "Plant_Specific_Max_pChEMBL",
            "Plant_Specific_Mean_pChEMBL",
            "Plant_Specific_Median_pChEMBL",
        ]
    )


# ============================================================
# 7. 상위 후보 생성
# ============================================================

print()
print("[7] T2D 상위 후보 생성")


top_columns = [
    "Plant_ID",
    "Scientific_Name",
    "Common_Name_KO",
    "Compound_Name",
    "ChEMBL_ID",
    "Gene_Name",
    "Protein_Name",
    "UniProt_ID",
    "Predicted_pChEMBL",
    "Plant_Count",
    "Plant_Specific",
    "Target_Evidence",
    "Target_Role",
]


top_columns = [
    c
    for c in top_columns
    if c in t2d.columns
]


top_candidates = t2d[
    top_columns
].copy()


top_candidates = top_candidates.sort_values(
    "Predicted_pChEMBL",
    ascending=False
)


top_candidates = top_candidates.head(100)


top_candidates.to_csv(
    OUTPUT_TOP,
    index=False,
    encoding="utf-8-sig"
)


# ============================================================
# 8. 결과 출력
# ============================================================

print()
print("=" * 70)
print("T2D 자동 식물 분석 완료")
print("=" * 70)


print()
print("전체 요약")
print("-" * 70)
print(
    f"분석 식물 수: {len(summary)}"
)
print(
    f"T2D 예측 행: {len(t2d):,}"
)
print(
    f"T2D 화합물 수: "
    f"{t2d['ChEMBL_ID'].nunique():,}"
)
print(
    f"T2D 표적 수: "
    f"{t2d['UniProt_ID'].nunique():,}"
)


print()
print("출력 파일")
print("-" * 70)
print(f"전체 식물 요약: {OUTPUT_SUMMARY}")
print(f"식물 특이적 결과: {OUTPUT_SPECIFIC}")
print(f"상위 후보: {OUTPUT_TOP}")


# ============================================================
# 9. 상위 식물
# ============================================================

print()
print("=" * 70)
print("T2D 상위 식물 20개")
print("=" * 70)


print(
    summary[
        [
            "Plant_ID",
            "Scientific_Name",
            "T2D_Compound_Count",
            "T2D_Target_Count",
            "Max_Predicted_pChEMBL",
            "Mean_Predicted_pChEMBL",
        ]
    ]
    .head(20)
    .to_string(index=False)
)


# ============================================================
# 10. 식물 특이적 상위 후보
# ============================================================

print()
print("=" * 70)
print("식물 특이적 상위 후보 20개")
print("=" * 70)


if len(specific) > 0:

    print(
        specific[
            [
                "Plant_ID",
                "Scientific_Name",
                "Compound_Name",
                "ChEMBL_ID",
                "Gene_Name",
                "Predicted_pChEMBL",
                "Plant_Count",
            ]
        ]
        .head(20)
        .to_string(index=False)
    )


# ============================================================
# 11. 식물 특이적 화합물 기준 상위 식물
# ============================================================

print()
print("=" * 70)
print("식물 특이적 화합물 기준 상위 식물 20개")
print("=" * 70)


if len(specific_summary) > 0:

    print(
        specific_summary[
            [
                "Plant_ID",
                "Scientific_Name",
                "Plant_Specific_Compound_Count",
                "Plant_Specific_Target_Count",
                "Plant_Specific_Max_pChEMBL",
                "Plant_Specific_Mean_pChEMBL",
            ]
        ]
        .head(20)
        .to_string(index=False)
    )


# ============================================================
# 12. 자동 추가 식물 확인
# ============================================================

print()
print("=" * 70)
print("현재 자동 분석된 식물")
print("=" * 70)


plant_list = (
    summary[
        ["Plant_ID", "Scientific_Name"]
    ]
    .drop_duplicates()
    .sort_values("Plant_ID")
)


print(
    plant_list.to_string(index=False)
)


print()
print("=" * 70)
print("완료")
print("=" * 70)
