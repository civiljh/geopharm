import os
import joblib
import pandas as pd


BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)


# ============================================================
# GeoPharm
# 새 약용식물 범용 AI 예측
#
# 특정 식물 이름을 코드에 넣지 않는다.
# 입력 파일에 들어 있는 Plant_ID를 자동으로 처리한다.
# ============================================================


INPUT_FILE = os.path.join(
    BASE_DIR,
    "data",
    "processed",
    "external_plant_ai_prediction_ready.csv"
)


PROTEIN_FILE = os.path.join(
    BASE_DIR,
    "data",
    "processed",
    "protein_features.csv"
)


MODEL_FILE = os.path.join(
    BASE_DIR,
    "data",
    "processed",
    "random_forest_ic50_protein.joblib"
)


OUTPUT_FILE = os.path.join(
    BASE_DIR,
    "data",
    "processed",
    "external_plant_ai_predictions.csv"
)


print("=" * 70)
print("GeoPharm - 새 약용식물 AI 예측")
print("=" * 70)


# ============================================================
# 1. 파일 확인
# ============================================================

for file_path in [
    INPUT_FILE,
    PROTEIN_FILE,
    MODEL_FILE
]:

    if not os.path.exists(file_path):

        raise FileNotFoundError(
            f"필요한 파일을 찾을 수 없습니다:\n{file_path}"
        )


# ============================================================
# 2. AI 입력 데이터 읽기
# ============================================================

df = pd.read_csv(
    INPUT_FILE,
    encoding="utf-8-sig"
)


print()
print("=" * 70)
print("AI 입력 데이터")
print("=" * 70)

print(
    "입력 행:",
    len(df)
)


# ============================================================
# 3. 식물 확인
# ============================================================

if "Plant_ID" not in df.columns:

    raise ValueError(
        "AI 입력 데이터에 Plant_ID가 없습니다."
    )


print(
    "식물:",
    df["Plant_ID"].nunique()
)


print(
    "성분:",
    df["ChEMBL_ID"].nunique()
)


# ============================================================
# 4. Protein 데이터 읽기
# ============================================================

protein_df = pd.read_csv(
    PROTEIN_FILE,
    encoding="utf-8-sig"
)


print()
print("=" * 70)
print("Protein 데이터")
print("=" * 70)

print(
    "Protein 행:",
    len(protein_df)
)

print(
    "Protein 컬럼:",
    len(protein_df.columns)
)


if "UniProt_ID" not in protein_df.columns:

    raise ValueError(
        "protein_features.csv에 UniProt_ID가 없습니다."
    )


# ============================================================
# 5. Protein Feature 확인
# ============================================================

protein_feature_cols = [
    column
    for column in protein_df.columns
    if column != "UniProt_ID"
]


print(
    "Protein Feature:",
    len(protein_feature_cols)
)


if len(protein_feature_cols) != 26:

    raise ValueError(
        "Protein Feature가 26개가 아닙니다."
    )


# ============================================================
# 6. AI 모델 불러오기
# ============================================================

print()
print("=" * 70)
print("AI 모델")
print("=" * 70)

print(
    "모델:",
    os.path.relpath(
        MODEL_FILE,
        BASE_DIR
    )
)


model = joblib.load(
    MODEL_FILE
)


print(
    "모델 로드 완료"
)


# ============================================================
# 7. Morgan Feature 확인
# ============================================================

morgan_cols = [
    column
    for column in df.columns
    if column.startswith("Morgan_")
]


print()
print(
    "Morgan Feature:",
    len(morgan_cols)
)


if len(morgan_cols) != 2048:

    raise ValueError(
        "Morgan Feature가 2048개가 아닙니다."
    )


# ============================================================
# 8. Protein Feature 연결
# ============================================================

print()
print("=" * 70)
print("Protein Feature 연결")
print("=" * 70)


protein_merge = protein_df[
    ["UniProt_ID"] +
    protein_feature_cols
].copy()


protein_merge = protein_merge.drop_duplicates(
    subset=["UniProt_ID"]
)


df = df.merge(
    protein_merge,
    on="UniProt_ID",
    how="left",
    suffixes=(
        "",
        "_protein"
    )
)


# ============================================================
# 9. Protein Feature 결측값 확인
# ============================================================

missing_protein = (
    df[protein_feature_cols]
    .isna()
    .any(axis=1)
    .sum()
)


print(
    "Protein Feature 결측 행:",
    missing_protein
)


if missing_protein > 0:

    missing_ids = (
        df.loc[
            df[protein_feature_cols]
            .isna()
            .any(axis=1),
            ["UniProt_ID"]
        ]
        .drop_duplicates()
    )

    print()
    print(
        "Feature를 찾지 못한 UniProt:"
    )

    print(
        missing_ids.head(20)
        .to_string(index=False)
    )

    raise ValueError(
        "Protein Feature 결측"
    )


# ============================================================
# 10. 전체 AI Feature 구성
#
# Morgan 2048
# +
# Protein 26
# =
# 2074
# ============================================================

feature_cols = (
    morgan_cols +
    protein_feature_cols
)


print()
print(
    "전체 AI Feature:",
    len(feature_cols)
)


if len(feature_cols) != 2074:

    raise ValueError(
        "전체 AI Feature가 2074개가 아닙니다."
    )


# ============================================================
# 11. 모델 Feature 이름 확인
# ============================================================

if hasattr(
    model,
    "feature_names_in_"
):

    model_features = list(
        model.feature_names_in_
    )


    if model_features != feature_cols:

        print()
        print(
            "ERROR: 모델 Feature와 현재 Feature가 다릅니다."
        )


        missing = [
            column
            for column in model_features
            if column not in feature_cols
        ]


        extra = [
            column
            for column in feature_cols
            if column not in model_features
        ]


        if missing:

            print()
            print(
                "모델에는 있지만 현재 데이터에 없는 Feature:"
            )

            print(
                missing[:20]
            )


        if extra:

            print()
            print(
                "현재 데이터에는 있지만 모델에 없는 Feature:"
            )

            print(
                extra[:20]
            )


        raise ValueError(
            "AI Feature 구성이 모델과 일치하지 않습니다."
        )


# ============================================================
# 12. AI 예측
# ============================================================

print()
print("=" * 70)
print("AI 예측 시작")
print("=" * 70)


X = df[
    feature_cols
].astype(float)


print(
    "예측 입력 크기:",
    X.shape
)


predictions = model.predict(
    X
)


df[
    "Predicted_pChEMBL"
] = predictions


# ============================================================
# 13. 결과 정리
# ============================================================

result_cols = [
    "Plant_ID",
    "Common_Name_KO",
    "Scientific_Name",
    "KNApSAcK_ID",
    "Compound_Name",
    "ChEMBL_ID",
    "UniProt_ID",
    "Predicted_pChEMBL"
]


result_cols = [
    column
    for column in result_cols
    if column in df.columns
]


result = df[
    result_cols
].copy()


result = result.sort_values(
    "Predicted_pChEMBL",
    ascending=False
)


# ============================================================
# 14. 결과 저장
# ============================================================

result.to_csv(
    OUTPUT_FILE,
    index=False,
    encoding="utf-8-sig"
)


# ============================================================
# 15. 결과 출력
# ============================================================

print()
print("=" * 70)
print("AI 예측 완료")
print("=" * 70)


print(
    "전체 예측:",
    len(result)
)


print(
    "식물:",
    result["Plant_ID"].nunique()
)


print(
    "성분:",
    result["ChEMBL_ID"].nunique()
)


print(
    "Protein:",
    result["UniProt_ID"].nunique()
)


print()
print(
    "상위 20개 AI 예측"
)

print(
    "-" * 70
)


print(
    result[
        [
            "Plant_ID",
            "Compound_Name",
            "ChEMBL_ID",
            "UniProt_ID",
            "Predicted_pChEMBL"
        ]
    ]
    .head(20)
    .to_string(index=False)
)


print()
print(
    "저장 완료:"
)

print(
    os.path.relpath(
        OUTPUT_FILE,
        BASE_DIR
    )
)


print()
print("=" * 70)