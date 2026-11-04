import pandas as pd
from sklearn.model_selection import GroupShuffleSplit

INPUT_FILE = "data/processed/ml_dataset.csv"
TRAIN_FILE = "data/processed/ic50_train.csv"
TEST_FILE = "data/processed/ic50_test.csv"

# --------------------------------------------------
# 1. ML 데이터 불러오기
# --------------------------------------------------

df = pd.read_csv(INPUT_FILE)

# IC50만 사용
df = df[
    df["Standard_Type"] == "IC50"
].copy()

print("전체 IC50 행:", len(df))
print("전체 IC50 화합물:", df["ChEMBL_ID"].nunique())


# --------------------------------------------------
# 2. 화합물 기준 Train/Test 분할
# --------------------------------------------------

splitter = GroupShuffleSplit(
    n_splits=1,
    test_size=0.2,
    random_state=42
)

train_idx, test_idx = next(
    splitter.split(
        df,
        groups=df["ChEMBL_ID"]
    )
)

train = df.iloc[train_idx].copy()
test = df.iloc[test_idx].copy()


# --------------------------------------------------
# 3. 분할 결과 확인
# --------------------------------------------------

train_compounds = set(train["ChEMBL_ID"])
test_compounds = set(test["ChEMBL_ID"])

overlap = train_compounds & test_compounds

print()
print("Train 행:", len(train))
print("Test 행:", len(test))

print("Train 화합물:", len(train_compounds))
print("Test 화합물:", len(test_compounds))

print("Train/Test 화합물 중복:", len(overlap))


# --------------------------------------------------
# 4. 저장
# --------------------------------------------------

train.to_csv(
    TRAIN_FILE,
    index=False,
    encoding="utf-8-sig"
)

test.to_csv(
    TEST_FILE,
    index=False,
    encoding="utf-8-sig"
)

print()
print("Train/Test 분할 완료")
print("Train:", TRAIN_FILE)
print("Test:", TEST_FILE)