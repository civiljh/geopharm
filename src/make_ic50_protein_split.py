import pandas as pd


TRAIN_FILE = "data/processed/ic50_train.csv"
TEST_FILE = "data/processed/ic50_test.csv"
PROTEIN_FILE = "data/processed/protein_features.csv"

TRAIN_OUTPUT = "data/processed/ic50_protein_train.csv"
TEST_OUTPUT = "data/processed/ic50_protein_test.csv"


# --------------------------------------------------
# 1. 데이터 불러오기
# --------------------------------------------------

train = pd.read_csv(TRAIN_FILE)
test = pd.read_csv(TEST_FILE)
protein = pd.read_csv(PROTEIN_FILE)

print("기존 Train:", len(train))
print("기존 Test:", len(test))
print("Protein feature:", len(protein))


# --------------------------------------------------
# 2. Protein feature 목록
# --------------------------------------------------

protein_feature_columns = [
    column
    for column in protein.columns
    if column != "UniProt_ID"
]

print("Protein feature 수:", len(protein_feature_columns))


# --------------------------------------------------
# 3. Train에 Protein feature 연결
# --------------------------------------------------

train_protein = train.merge(
    protein,
    on="UniProt_ID",
    how="left",
    validate="many_to_one"
)


# --------------------------------------------------
# 4. Test에 Protein feature 연결
# --------------------------------------------------

test_protein = test.merge(
    protein,
    on="UniProt_ID",
    how="left",
    validate="many_to_one"
)


# --------------------------------------------------
# 5. 연결 상태 확인
# --------------------------------------------------

train_missing = train_protein[
    protein_feature_columns
].isna().any(axis=1)

test_missing = test_protein[
    protein_feature_columns
].isna().any(axis=1)


print()
print("===== Train Protein 연결 =====")
print("행:", len(train_protein))
print("연결 성공:", (~train_missing).sum())
print("연결 실패:", train_missing.sum())


print()
print("===== Test Protein 연결 =====")
print("행:", len(test_protein))
print("연결 성공:", (~test_missing).sum())
print("연결 실패:", test_missing.sum())


# --------------------------------------------------
# 6. Train/Test 화합물 중복 확인
# --------------------------------------------------

train_compounds = set(train_protein["ChEMBL_ID"])
test_compounds = set(test_protein["ChEMBL_ID"])

overlap = train_compounds & test_compounds

print()
print("===== 화합물 분할 확인 =====")
print("Train 화합물:", len(train_compounds))
print("Test 화합물:", len(test_compounds))
print("Train/Test 화합물 중복:", len(overlap))


# --------------------------------------------------
# 7. 저장
# --------------------------------------------------

train_protein.to_csv(
    TRAIN_OUTPUT,
    index=False,
    encoding="utf-8-sig"
)

test_protein.to_csv(
    TEST_OUTPUT,
    index=False,
    encoding="utf-8-sig"
)


print()
print("Protein-aware Train/Test 생성 완료")
print("Train:", TRAIN_OUTPUT)
print("Test:", TEST_OUTPUT)