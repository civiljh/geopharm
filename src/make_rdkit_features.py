import pandas as pd

from rdkit import Chem
from rdkit.Chem import rdFingerprintGenerator


INPUT_FILE = "data/processed/plant_compounds_chembl.csv"
OUTPUT_FILE = "data/processed/rdkit_features.csv"


# ==================================================
# 1. 식물 화합물 데이터 읽기
# ==================================================

compounds = pd.read_csv(
    INPUT_FILE
)

print()
print("========================================")
print("식물 화합물 RDKit Feature 생성")
print("========================================")
print(
    "전체 입력 행:",
    len(compounds)
)


# ==================================================
# 2. ChEMBL ID + SMILES가 있는 화합물만 선택
# ==================================================

compounds = compounds[
    compounds["ChEMBL_ID"].notna() &
    compounds["ChEMBL_CanonicalSMILES"].notna()
].copy()


# 같은 ChEMBL_ID가 여러 식물에서 발견될 수 있으므로
# 화합물 자체의 Feature는 한 번만 생성한다.

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

morgan_generator = rdFingerprintGenerator.GetMorganGenerator(
    radius=2,
    fpSize=2048
)


# ==================================================
# 4. RDKit Feature 생성
# ==================================================

feature_rows = []

success_count = 0
failed_count = 0


for _, row in compounds.iterrows():

    chembl_id = row["ChEMBL_ID"]
    smiles = row["ChEMBL_CanonicalSMILES"]

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


        fingerprint = morgan_generator.GetFingerprint(
            mol
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
print("========================================")
print("RDKit Feature 생성 완료")
print("========================================")

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
    "Feature 수:",
    len(features.columns)
)

print(
    "예상 Feature:",
    2049
)

print(
    "저장:",
    OUTPUT_FILE
)

print("========================================")