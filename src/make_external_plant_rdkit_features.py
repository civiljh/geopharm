import pandas as pd

from rdkit import Chem
from rdkit.Chem import rdFingerprintGenerator

import os


INPUT_FILE = "data/processed/external_plant_compounds_chembl.csv"
OUTPUT_FILE = "data/processed/external_plant_rdkit_features.csv"


# ==================================================
# 1. 입력 파일 확인
# ==================================================

if not os.path.exists(INPUT_FILE):

    print()
    print("ERROR: 입력 파일을 찾을 수 없습니다.")
    print(INPUT_FILE)
    raise SystemExit


compounds = pd.read_csv(
    INPUT_FILE,
    encoding="utf-8-sig"
)


print()
print("=" * 70)
print("GeoPharm - 외부 식물 RDKit Feature 생성")
print("=" * 70)

print()
print("전체 입력:", len(compounds))


# ==================================================
# 2. ChEMBL ID + PubChem SMILES가 있는 화합물만 선택
# ==================================================

compounds = compounds[
    compounds["ChEMBL_ID"].notna() &
    compounds["PubChem_SMILES"].notna()
].copy()


compounds = compounds[
    compounds["ChEMBL_ID"].astype(str).str.strip() != ""
].copy()


compounds = compounds[
    compounds["PubChem_SMILES"].astype(str).str.strip() != ""
].copy()


# 같은 ChEMBL ID는 한 번만 처리

compounds = compounds.drop_duplicates(
    subset=["ChEMBL_ID"]
).copy()


print(
    "ChEMBL + SMILES가 있는 고유 화합물:",
    len(compounds)
)


# ==================================================
# 3. Morgan Fingerprint 생성기
# ==================================================

morgan_generator = (
    rdFingerprintGenerator.GetMorganGenerator(
        radius=2,
        fpSize=2048
    )
)


# ==================================================
# 4. RDKit Feature 생성
# ==================================================

feature_rows = []

success_count = 0
failed_count = 0


for _, row in compounds.iterrows():

    chembl_id = row["ChEMBL_ID"]
    smiles = row["PubChem_SMILES"]

    try:

        mol = Chem.MolFromSmiles(
            smiles
        )

        if mol is None:

            print(
                "RDKit 구조 변환 실패:",
                chembl_id
            )

            failed_count += 1
            continue


        fingerprint = (
            morgan_generator.GetFingerprint(
                mol
            )
        )


        descriptors = {
            "ChEMBL_ID": chembl_id
        }


        # Morgan 2048개 Feature

        for i in range(
            fingerprint.GetNumBits()
        ):

            descriptors[
                f"Morgan_{i}"
            ] = int(
                fingerprint[i]
            )


        feature_rows.append(
            descriptors
        )

        success_count += 1


    except Exception as e:

        print(
            "RDKit 처리 오류:",
            chembl_id,
            e
        )

        failed_count += 1


# ==================================================
# 5. 결과 DataFrame 생성
# ==================================================

features = pd.DataFrame(
    feature_rows
)


# ==================================================
# 6. 결과 저장
# ==================================================

features.to_csv(
    OUTPUT_FILE,
    index=False,
    encoding="utf-8-sig"
)


# ==================================================
# 7. 결과 출력
# ==================================================

print()
print("=" * 70)
print("RDKit Feature 생성 완료")
print("=" * 70)

print(
    "입력 고유 화합물:",
    len(compounds)
)

print(
    "RDKit 성공:",
    success_count
)

print(
    "RDKit 실패:",
    failed_count
)

print(
    "최종 Feature 행:",
    len(features)
)

print(
    "Feature 열:",
    len(features.columns)
)

print(
    "예상 Feature 열:",
    2049
)

print()
print("저장:")
print(OUTPUT_FILE)

print()
print("=" * 70)