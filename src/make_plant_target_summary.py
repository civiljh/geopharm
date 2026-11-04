import pandas as pd


INPUT_FILE = "data/processed/plant_ai_connection_normalized.csv"

OUTPUT_FILE = "data/processed/plant_target_summary.csv"


# ==================================================
# 1. 데이터 불러오기
# ==================================================

df = pd.read_csv(INPUT_FILE)

print("========================================")
print("식물-AI 연결 데이터")
print("========================================")
print("전체 행:", len(df))


# ==================================================
# 2. 필요한 데이터 확인
# ==================================================

required_columns = [
    "Plant_ID",
    "Scientific_Name",
    "ChEMBL_ID",
    "Compound_Name",
    "UniProt_ID",
    "Standard_Type",
    "pChEMBL"
]

missing_columns = [
    column
    for column in required_columns
    if column not in df.columns
]

if missing_columns:
    print()
    print("필수 컬럼이 없습니다:")
    print(missing_columns)
    raise SystemExit


# ==================================================
# 3. pChEMBL 숫자 변환
# ==================================================

df["pChEMBL"] = pd.to_numeric(
    df["pChEMBL"],
    errors="coerce"
)


# ==================================================
# 4. 식물-화합물-단백질 관계 중복 제거
# ==================================================

df = df.drop_duplicates(
    subset=[
        "Plant_ID",
        "ChEMBL_ID",
        "UniProt_ID",
        "Standard_Type",
        "pChEMBL"
    ]
).copy()


print()
print("중복 제거 후:", len(df))


# ==================================================
# 5. 식물별 화합물-단백질 연결 요약
# ==================================================

summary = (
    df
    .groupby(
        [
            "Plant_ID",
            "Scientific_Name",
            "ChEMBL_ID",
            "Compound_Name",
            "UniProt_ID"
        ],
        dropna=False
    )
    .agg(
        Measurement_Count=(
            "pChEMBL",
            "count"
        ),
        Mean_pChEMBL=(
            "pChEMBL",
            "mean"
        ),
        Max_pChEMBL=(
            "pChEMBL",
            "max"
        ),
        Min_pChEMBL=(
            "pChEMBL",
            "min"
        )
    )
    .reset_index()
)


# ==================================================
# 6. 결과 정렬
# ==================================================

summary = summary.sort_values(
    [
        "Plant_ID",
        "Max_pChEMBL"
    ],
    ascending=[
        True,
        False
    ]
).reset_index(drop=True)


# ==================================================
# 7. 식물별 최고 affinity 후보
# ==================================================

print()
print("========================================")
print("식물별 최고 pChEMBL 후보")
print("========================================")

best_by_plant = (
    summary
    .sort_values(
        [
            "Plant_ID",
            "Max_pChEMBL"
        ],
        ascending=[
            True,
            False
        ]
    )
    .groupby(
        "Plant_ID"
    )
    .head(5)
)

print(
    best_by_plant[
        [
            "Plant_ID",
            "Scientific_Name",
            "ChEMBL_ID",
            "Compound_Name",
            "UniProt_ID",
            "Max_pChEMBL"
        ]
    ].to_string(index=False)
)


# ==================================================
# 8. 전체 요약
# ==================================================

print()
print("========================================")
print("최종 요약")
print("========================================")

print(
    "식물:",
    summary["Plant_ID"].nunique()
)

print(
    "화합물:",
    summary["ChEMBL_ID"].nunique()
)

print(
    "단백질:",
    summary["UniProt_ID"].nunique()
)

print(
    "화합물-단백질 관계:",
    len(summary)
)


# ==================================================
# 9. 저장
# ==================================================

summary.to_csv(
    OUTPUT_FILE,
    index=False,
    encoding="utf-8-sig"
)

print()
print("========================================")
print("식물-표적 요약 생성 완료")
print("========================================")
print("행:", len(summary))
print("저장:", OUTPUT_FILE)