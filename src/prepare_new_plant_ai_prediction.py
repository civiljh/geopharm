import pandas as pd
import os


INPUT_FILE = "data/processed/new_plant_compounds_chembl_retry.csv"
RDKIT_FILE = "data/processed/new_plant_rdkit_features.csv"
PROTEIN_FILE = "data/processed/protein_features.csv"

OUTPUT_FILE = "data/processed/new_plant_ai_prediction_ready.csv"


# ==================================================
# 1. 파일 확인
# ==================================================

for file_path in [
    INPUT_FILE,
    RDKIT_FILE,
    PROTEIN_FILE
]:

    if not os.path.exists(file_path):

        print()
        print("ERROR: 파일을 찾을 수 없습니다.")
        print(file_path)
        raise SystemExit


# ==================================================
# 2. 데이터 읽기
# ==================================================

plant = pd.read_csv(
    INPUT_FILE,
    encoding="utf-8-sig"
)

rdkit = pd.read_csv(
    RDKIT_FILE,
    encoding="utf-8-sig"
)

protein = pd.read_csv(
    PROTEIN_FILE,
    encoding="utf-8-sig"
)


print()
print("=" * 70)
print("GeoPharm - 새 약용식물 AI 예측 준비")
print("=" * 70)

print()
print("새 약용식물 화합물:", len(plant))
print("새 약용식물 RDKit:", len(rdkit))
print("Protein:", len(protein))


# ==================================================
# 3. RDKit 연결에 필요한 컬럼 확인
# ==================================================

required_plant_columns = [
    "Plant_ID",
    "KNApSAcK_ID"
]

required_rdkit_columns = [
    "Plant_ID",
    "KNApSAcK_ID"
]


for column in required_plant_columns:

    if column not in plant.columns:

        raise SystemExit(
            f"원본 데이터에 {column} 컬럼이 없습니다."
        )


for column in required_rdkit_columns:

    if column not in rdkit.columns:

        raise SystemExit(
            f"RDKit 데이터에 {column} 컬럼이 없습니다."
        )


# ==================================================
# 4. PubChem SMILES가 있는 화합물 확인
# ==================================================

if "PubChem_SMILES" not in plant.columns:

    raise SystemExit(
        "원본 데이터에 PubChem_SMILES 컬럼이 없습니다."
    )


plant["PubChem_SMILES"] = (
    plant["PubChem_SMILES"]
    .fillna("")
    .astype(str)
    .str.strip()
)

plant = plant[
    plant["PubChem_SMILES"] != ""
].copy()


print()
print(
    "PubChem SMILES가 있는 화합물:",
    len(plant)
)


# ==================================================
# 5. RDKit Feature 확인
# ==================================================

morgan_columns = [
    column
    for column in rdkit.columns
    if column.startswith("Morgan_")
]


print()
print(
    "Morgan Feature:",
    len(morgan_columns)
)


if len(morgan_columns) != 2048:

    raise SystemExit(
        "Morgan Feature가 2048개가 아닙니다."
    )


# ==================================================
# 6. RDKit Feature 연결
# ==================================================

rdkit_merge_columns = [
    "Plant_ID",
    "KNApSAcK_ID"
] + morgan_columns


plant = plant.merge(
    rdkit[
        rdkit_merge_columns
    ],
    on=[
        "Plant_ID",
        "KNApSAcK_ID"
    ],
    how="inner",
    validate="many_to_one"
)


print()
print("=" * 70)
print("식물 화합물 + RDKit 연결")
print("=" * 70)

print(
    "연결 후 화합물:",
    len(plant)
)

print(
    "식물:",
    plant["Plant_ID"].nunique()
)

print(
    "KNApSAcK:",
    plant["KNApSAcK_ID"].nunique()
)


if len(plant) == 0:

    raise SystemExit(
        "RDKit Feature와 연결된 화합물이 없습니다."
    )


# ==================================================
# 7. Protein Feature 확인
# ==================================================

if "UniProt_ID" not in protein.columns:

    raise SystemExit(
        "protein_features.csv에 UniProt_ID 컬럼이 없습니다."
    )


protein_feature_columns = [
    column
    for column in protein.columns
    if column != "UniProt_ID"
]


print()
print(
    "Protein Feature:",
    len(protein_feature_columns)
)


if len(protein_feature_columns) != 26:

    raise SystemExit(
        f"Protein Feature가 26개가 아닙니다. "
        f"현재: {len(protein_feature_columns)}"
    )


# ==================================================
# 8. Protein과 조합
# ==================================================

plant["_merge_key"] = 1
protein["_merge_key"] = 1


prediction_input = pd.merge(
    plant,
    protein,
    on="_merge_key",
    how="inner"
)


prediction_input = prediction_input.drop(
    columns=["_merge_key"]
)


print()
print("=" * 70)
print("새 약용식물 AI 예측 조합")
print("=" * 70)

print(
    "예측 조합:",
    len(prediction_input)
)

print(
    "식물:",
    prediction_input["Plant_ID"].nunique()
)

print(
    "화합물:",
    prediction_input["KNApSAcK_ID"].nunique()
)

print(
    "Protein:",
    prediction_input["UniProt_ID"].nunique()
)


# ==================================================
# 9. AI Feature 확인
# ==================================================

feature_columns = (
    morgan_columns +
    protein_feature_columns
)


print()
print(
    "전체 AI Feature:",
    len(feature_columns)
)


if len(feature_columns) != 2074:

    raise SystemExit(
        f"AI Feature가 2074개가 아닙니다. "
        f"현재: {len(feature_columns)}"
    )


# ==================================================
# 10. 결측값 확인
# ==================================================

X = prediction_input[
    feature_columns
].copy()


missing = X.isna().any(axis=1)


print()
print("=" * 70)
print("결측값 검사")
print("=" * 70)

print(
    "정상 행:",
    (~missing).sum()
)

print(
    "결측 행:",
    missing.sum()
)


if missing.sum() > 0:

    prediction_input = prediction_input.loc[
        ~missing
    ].copy()


# ==================================================
# 11. 결과 저장
# ==================================================

prediction_input.to_csv(
    OUTPUT_FILE,
    index=False,
    encoding="utf-8-sig"
)


# ==================================================
# 12. 결과 출력
# ==================================================

print()
print("=" * 70)
print("새 약용식물 AI 예측 준비 완료")
print("=" * 70)

print(
    "최종 입력 행:",
    len(prediction_input)
)

print(
    "AI Feature:",
    len(feature_columns)
)

print()
print(
    "저장 파일:"
)

print(
    OUTPUT_FILE
)

print()
print("=" * 70)