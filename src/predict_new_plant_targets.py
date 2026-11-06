import os
import joblib
import pandas as pd
import numpy as np


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

INPUT_FILE = os.path.join(
    BASE_DIR,
    "data",
    "processed",
    "new_plant_ai_prediction_ready.csv"
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
    "new_plant_ai_predictions.csv"
)


print("=" * 70)
print("GeoPharm - 새 식물 AI 예측")
print("=" * 70)


# ------------------------------------------------------------
# 1. AI 입력 데이터
# ------------------------------------------------------------
df = pd.read_csv(INPUT_FILE)

print()
print(f"AI 입력 행: {len(df)}")


# ------------------------------------------------------------
# 2. 단백질 특징 데이터
# ------------------------------------------------------------
print()
print("=" * 70)
print("단백질 특징")
print("=" * 70)

protein_df = pd.read_csv(PROTEIN_FILE)

print(f"단백질 행: {len(protein_df)}")
print(f"단백질 열: {len(protein_df.columns)}")


if "UniProt_ID" not in protein_df.columns:
    raise ValueError("protein_features.csv에 UniProt_ID 열이 없습니다.")


# UniProt_ID를 제외한 나머지 열이 AI용 단백질 특징 26개
protein_feature_cols = [
    c for c in protein_df.columns
    if c != "UniProt_ID"
]


print(f"AI용 Protein Feature: {len(protein_feature_cols)}")


if len(protein_feature_cols) != 26:
    raise ValueError(
        f"Protein Feature가 26개가 아닙니다. "
        f"현재: {len(protein_feature_cols)}"
    )


# ------------------------------------------------------------
# 3. AI 모델
# ------------------------------------------------------------
print()
print("=" * 70)
print("AI 모델")
print("=" * 70)

print(f"모델: {os.path.relpath(MODEL_FILE, BASE_DIR)}")

model = joblib.load(MODEL_FILE)

print("모델 로드 완료")


# ------------------------------------------------------------
# 4. Morgan Feature 확인
# ------------------------------------------------------------
morgan_cols = [
    c for c in df.columns
    if c.startswith("Morgan_")
]

print()
print(f"Morgan Feature: {len(morgan_cols)}")

if len(morgan_cols) != 2048:
    raise ValueError(
        f"Morgan Feature가 2048개가 아닙니다. "
        f"현재: {len(morgan_cols)}"
    )


# ------------------------------------------------------------
# 5. 단백질 특징 + 식물 화합물 연결
# ------------------------------------------------------------
print()
print("=" * 70)
print("AI 입력 데이터 구성")
print("=" * 70)

# UniProt_ID를 기준으로 단백질 특징 연결
protein_merge = protein_df[
    ["UniProt_ID"] + protein_feature_cols
].copy()


df = df.merge(
    protein_merge,
    on="UniProt_ID",
    how="left",
    suffixes=("", "_protein")
)


# ------------------------------------------------------------
# 6. 단백질 특징 누락 확인
# ------------------------------------------------------------
missing_protein = df[protein_feature_cols].isna().any(axis=1).sum()

print(f"단백질 특징 누락 행: {missing_protein}")

if missing_protein > 0:
    print("ERROR: 일부 UniProt 단백질의 특징값을 찾지 못했습니다.")
    print(
        df.loc[
            df[protein_feature_cols].isna().any(axis=1),
            ["UniProt_ID"]
        ].drop_duplicates().head(20)
    )
    raise ValueError("단백질 특징 누락")


# ------------------------------------------------------------
# 7. AI 입력 Feature 구성
# ------------------------------------------------------------
feature_cols = morgan_cols + protein_feature_cols

print()
print(f"전체 AI Feature: {len(feature_cols)}")


if len(feature_cols) != 2074:
    raise ValueError(
        f"AI Feature가 2074개가 아닙니다. "
        f"현재: {len(feature_cols)}"
    )


# ------------------------------------------------------------
# 8. 모델 Feature 이름 확인
# ------------------------------------------------------------
if hasattr(model, "feature_names_in_"):

    model_features = list(model.feature_names_in_)

    if model_features != feature_cols:
        print()
        print("모델 Feature 이름 순서를 확인합니다.")

        missing = [
            c for c in model_features
            if c not in feature_cols
        ]

        extra = [
            c for c in feature_cols
            if c not in model_features
        ]

        if missing:
            print("모델에는 있지만 현재 데이터에 없는 Feature:")
            print(missing[:20])

        if extra:
            print("현재 데이터에는 있지만 모델에 없는 Feature:")
            print(extra[:20])

        raise ValueError(
            "현재 AI Feature 구성이 학습된 모델과 일치하지 않습니다."
        )


# ------------------------------------------------------------
# 9. AI 예측
# ------------------------------------------------------------
print()
print("=" * 70)
print("AI 예측 시작")
print("=" * 70)

X = df[feature_cols].astype(float)

print(f"예측 입력 크기: {X.shape}")

predictions = model.predict(X)

df["Predicted_pChEMBL"] = predictions


# ------------------------------------------------------------
# 10. 결과 정리
# ------------------------------------------------------------
result_cols = [
    "Plant_ID",
    "Common_Name_KO",
    "Scientific_Name",
    "KNApSAcK_ID",
    "Compound_Name",
    "ChEMBL_ID",
    "InChIKey",
    "PubChem_CID",
    "UniProt_ID",
    "Predicted_pChEMBL",
]

result_cols = [
    c for c in result_cols
    if c in df.columns
]

result = df[result_cols].copy()

result = result.sort_values(
    "Predicted_pChEMBL",
    ascending=False
)


# ------------------------------------------------------------
# 11. 저장
# ------------------------------------------------------------
result.to_csv(
    OUTPUT_FILE,
    index=False,
    encoding="utf-8-sig"
)


# ------------------------------------------------------------
# 12. 결과 출력
# ------------------------------------------------------------
print()
print("=" * 70)
print("AI 예측 완료")
print("=" * 70)

print(f"전체 예측 행: {len(result)}")
print(f"식물 수: {result['Plant_ID'].nunique()}")
print(f"화합물 수: {result['ChEMBL_ID'].nunique()}")
print(f"단백질 수: {result['UniProt_ID'].nunique()}")

print()
print("AI 예측 결과 상위 20개")
print("-" * 70)

print(
    result[
        [
            "Plant_ID",
            "Compound_Name",
            "ChEMBL_ID",
            "UniProt_ID",
            "Predicted_pChEMBL",
        ]
    ].head(20).to_string(index=False)
)

print()
print(f"저장 완료: {os.path.relpath(OUTPUT_FILE, BASE_DIR)}")
