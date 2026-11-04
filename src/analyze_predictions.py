import pandas as pd


BASELINE_FILE = "data/processed/random_forest_ic50_predictions.csv"
PROTEIN_FILE = "data/processed/random_forest_ic50_protein_predictions.csv"

OUTPUT_FILE = "data/processed/prediction_analysis.csv"


# ==================================================
# 1. 데이터 불러오기
# ==================================================

baseline = pd.read_csv(BASELINE_FILE)
protein = pd.read_csv(PROTEIN_FILE)

print("========================================")
print("예측 데이터 불러오기")
print("========================================")
print("Compound-only:", len(baseline))
print("Compound + Protein:", len(protein))


# ==================================================
# 2. 분석용 컬럼 생성
# ==================================================

baseline = baseline.copy()
protein = protein.copy()

baseline["Absolute_Error"] = (
    baseline["pChEMBL"]
    - baseline["Predicted_pChEMBL"]
).abs()

protein["Absolute_Error"] = (
    protein["pChEMBL"]
    - protein["Predicted_pChEMBL"]
).abs()


# ==================================================
# 3. 실제값 통계
# ==================================================

print()
print("========================================")
print("실제 pChEMBL 통계")
print("========================================")

print(
    baseline["pChEMBL"].describe()
)


# ==================================================
# 4. 예측값 통계
# ==================================================

print()
print("========================================")
print("Compound-only 예측값 통계")
print("========================================")

print(
    baseline["Predicted_pChEMBL"].describe()
)

print()
print("========================================")
print("Compound + Protein 예측값 통계")
print("========================================")

print(
    protein["Predicted_pChEMBL"].describe()
)


# ==================================================
# 5. 가장 정확한 예측
# ==================================================

print()
print("========================================")
print("Compound-only 가장 정확한 예측 TOP 10")
print("========================================")

best_baseline = baseline.sort_values(
    "Absolute_Error"
).head(10)

print(
    best_baseline[
        [
            "ChEMBL_ID",
            "UniProt_ID",
            "pChEMBL",
            "Predicted_pChEMBL",
            "Absolute_Error"
        ]
    ].to_string(index=False)
)


print()
print("========================================")
print("Compound + Protein 가장 정확한 예측 TOP 10")
print("========================================")

best_protein = protein.sort_values(
    "Absolute_Error"
).head(10)

print(
    best_protein[
        [
            "ChEMBL_ID",
            "UniProt_ID",
            "pChEMBL",
            "Predicted_pChEMBL",
            "Absolute_Error"
        ]
    ].to_string(index=False)
)


# ==================================================
# 6. 오차가 가장 큰 예측
# ==================================================

print()
print("========================================")
print("Compound-only 오차가 큰 예측 TOP 10")
print("========================================")

worst_baseline = baseline.sort_values(
    "Absolute_Error",
    ascending=False
).head(10)

print(
    worst_baseline[
        [
            "ChEMBL_ID",
            "UniProt_ID",
            "pChEMBL",
            "Predicted_pChEMBL",
            "Absolute_Error"
        ]
    ].to_string(index=False)
)


print()
print("========================================")
print("Compound + Protein 오차가 큰 예측 TOP 10")
print("========================================")

worst_protein = protein.sort_values(
    "Absolute_Error",
    ascending=False
).head(10)

print(
    worst_protein[
        [
            "ChEMBL_ID",
            "UniProt_ID",
            "pChEMBL",
            "Predicted_pChEMBL",
            "Absolute_Error"
        ]
    ].to_string(index=False)
)


# ==================================================
# 7. 같은 화합물의 단백질별 예측 차이
# ==================================================

print()
print("========================================")
print("같은 화합물의 단백질별 예측 차이")
print("========================================")

compound_counts = (
    protein
    .groupby("ChEMBL_ID")["UniProt_ID"]
    .nunique()
    .sort_values(ascending=False)
)

multi_target_compounds = compound_counts[
    compound_counts > 1
].index

print(
    "여러 단백질에 연결된 화합물:",
    len(multi_target_compounds)
)

if len(multi_target_compounds) > 0:

    example_compound = multi_target_compounds[0]

    example = protein[
        protein["ChEMBL_ID"] == example_compound
    ].copy()

    example = example.sort_values(
        "Predicted_pChEMBL",
        ascending=False
    )

    print()
    print("분석 예시 화합물:", example_compound)

    print(
        example[
            [
                "ChEMBL_ID",
                "UniProt_ID",
                "pChEMBL",
                "Predicted_pChEMBL",
                "Absolute_Error"
            ]
        ].to_string(index=False)
    )


# ==================================================
# 8. Compound-only vs Protein 모델의
#    동일 행 기준 오차 비교
# ==================================================

comparison = baseline[
    [
        "ChEMBL_ID",
        "UniProt_ID",
        "pChEMBL",
        "Predicted_pChEMBL",
        "Absolute_Error"
    ]
].copy()

comparison = comparison.rename(
    columns={
        "Predicted_pChEMBL":
            "CompoundOnly_Predicted_pChEMBL",
        "Absolute_Error":
            "CompoundOnly_Absolute_Error"
    }
)

protein_compare = protein[
    [
        "ChEMBL_ID",
        "UniProt_ID",
        "Predicted_pChEMBL",
        "Absolute_Error"
    ]
].copy()

protein_compare = protein_compare.rename(
    columns={
        "Predicted_pChEMBL":
            "Protein_Predicted_pChEMBL",
        "Absolute_Error":
            "Protein_Absolute_Error"
    }
)

comparison = comparison.merge(
    protein_compare,
    on=[
        "ChEMBL_ID",
        "UniProt_ID"
    ],
    how="inner"
)

comparison["Error_Difference"] = (
    comparison["CompoundOnly_Absolute_Error"]
    - comparison["Protein_Absolute_Error"]
)

comparison["Protein_Model_Better"] = (
    comparison["Protein_Absolute_Error"]
    < comparison["CompoundOnly_Absolute_Error"]
)


print()
print("========================================")
print("동일 샘플 기준 모델 비교")
print("========================================")

print(
    "비교 가능한 샘플:",
    len(comparison)
)

print(
    "Protein 모델이 더 정확한 샘플:",
    comparison["Protein_Model_Better"].sum()
)

print(
    "Compound-only가 더 정확한 샘플:",
    (
        ~comparison["Protein_Model_Better"]
    ).sum()
)

print()
print(
    "평균 Absolute Error 차이:"
)

print(
    comparison["Error_Difference"].mean()
)


# ==================================================
# 9. 결과 저장
# ==================================================

comparison.to_csv(
    OUTPUT_FILE,
    index=False,
    encoding="utf-8-sig"
)

print()
print("========================================")
print("분석 결과 저장 완료")
print("========================================")
print("저장 위치:", OUTPUT_FILE)