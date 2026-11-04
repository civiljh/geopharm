import os
import pandas as pd

from rdkit import Chem
from rdkit.Chem import rdFingerprintGenerator
from rdkit.Chem import Descriptors


BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

INPUT_FILE = os.path.join(
    BASE_DIR,
    "data",
    "processed",
    "new_plant_compounds_chembl_retry.csv"
)

OUTPUT_FILE = os.path.join(
    BASE_DIR,
    "data",
    "processed",
    "new_plant_rdkit_features.csv"
)


print("=" * 70)
print("GeoPharm - RDKit Feature 생성")
print("=" * 70)

print()
print("입력 파일:")
print(INPUT_FILE)


# ------------------------------------------------------------
# 1. 화합물 데이터 읽기
# ------------------------------------------------------------

compounds = pd.read_csv(
    INPUT_FILE,
    encoding="utf-8-sig"
)

print()
print(f"전체 화합물 수: {len(compounds)}")


# ------------------------------------------------------------
# 2. PubChem SMILES 확인
# ------------------------------------------------------------

if "PubChem_SMILES" not in compounds.columns:
    raise ValueError(
        "new_plant_compounds_chembl_retry.csv에 "
        "PubChem_SMILES 컬럼이 없습니다."
    )


# PubChem SMILES가 있는 화합물만 사용
compounds = compounds[
    compounds["PubChem_SMILES"].notna()
].copy()

compounds["PubChem_SMILES"] = (
    compounds["PubChem_SMILES"]
    .astype(str)
    .str.strip()
)

compounds = compounds[
    compounds["PubChem_SMILES"] != ""
].copy()


print(
    f"PubChem SMILES가 있는 화합물: {len(compounds)}"
)


if len(compounds) == 0:
    raise ValueError(
        "RDKit을 계산할 수 있는 PubChem SMILES가 없습니다."
    )


# ------------------------------------------------------------
# 3. RDKit Morgan Fingerprint 생성기
# ------------------------------------------------------------

morgan_generator = (
    rdFingerprintGenerator.GetMorganGenerator(
        radius=2,
        fpSize=2048
    )
)


# ------------------------------------------------------------
# 4. RDKit Feature 생성
# ------------------------------------------------------------

features = []

failed_count = 0

for _, row in compounds.iterrows():

    smiles = str(
        row["PubChem_SMILES"]
    ).strip()

    mol = Chem.MolFromSmiles(
        smiles
    )

    if mol is None:
        failed_count += 1
        continue

    # --------------------------------------------------------
    # 기본 정보
    # --------------------------------------------------------

    feature_row = {
        "Plant_ID": row.get(
            "Plant_ID",
            ""
        ),
        "KNApSAcK_ID": row.get(
            "KNApSAcK_ID",
            ""
        ),
        "Compound_Name": row.get(
            "Compound_Name",
            ""
        ),
        "PubChem_CID": row.get(
            "PubChem_CID",
            ""
        ),
        "ChEMBL_ID": row.get(
            "ChEMBL_ID",
            ""
        ),
        "InChIKey": row.get(
            "InChIKey",
            ""
        ),
        "PubChem_SMILES": smiles,

        # 기본 분자 특성
        "MolWt": Descriptors.MolWt(mol),
        "MolLogP": Descriptors.MolLogP(mol),
        "NumHDonors": Descriptors.NumHDonors(mol),
        "NumHAcceptors": Descriptors.NumHAcceptors(mol),
        "TPSA": Descriptors.TPSA(mol),
    }


    # --------------------------------------------------------
    # Morgan Fingerprint 2048개
    # --------------------------------------------------------

    fingerprint = (
        morgan_generator.GetFingerprint(mol)
    )

    for i in range(2048):

        feature_row[
            f"Morgan_{i}"
        ] = fingerprint[i]


    features.append(
        feature_row
    )


# ------------------------------------------------------------
# 5. 결과 DataFrame
# ------------------------------------------------------------

features = pd.DataFrame(
    features
)


print()
print(
    f"RDKit 생성 성공: {len(features)}"
)

print(
    f"RDKit 생성 실패: {failed_count}"
)


if len(features) == 0:
    raise ValueError(
        "RDKit Feature가 하나도 생성되지 않았습니다."
    )


# ------------------------------------------------------------
# 6. 저장
# ------------------------------------------------------------

features.to_csv(
    OUTPUT_FILE,
    index=False,
    encoding="utf-8-sig"
)


# ------------------------------------------------------------
# 7. 결과 확인
# ------------------------------------------------------------

morgan_columns = [
    column
    for column in features.columns
    if column.startswith("Morgan_")
]


print()
print("=" * 70)
print("RDKit Feature 생성 완료")
print("=" * 70)

print(
    f"결과 화합물 수: {len(features)}"
)

print(
    f"Morgan Feature 수: {len(morgan_columns)}"
)

print()
print(
    f"저장 파일: {OUTPUT_FILE}"
)