import pandas as pd


ML_FILE = "data/processed/ml_dataset.csv"
UNIPROT_FILE = "data/processed/uniprot_details.csv"
OUTPUT_FILE = "data/processed/ml_uniprot_details.csv"


# --------------------------------------------------
# 1. ML 데이터 불러오기
# --------------------------------------------------

ml = pd.read_csv(ML_FILE)

print("ML 데이터:", len(ml))


# --------------------------------------------------
# 2. ML에서 실제 사용하는 UniProt만 추출
# --------------------------------------------------

ml_uniprot_ids = (
    ml["UniProt_ID"]
    .dropna()
    .drop_duplicates()
)

print("ML에서 사용하는 고유 UniProt:", len(ml_uniprot_ids))


# --------------------------------------------------
# 3. UniProt 상세정보 불러오기
# --------------------------------------------------

uniprot = pd.read_csv(UNIPROT_FILE)

print("UniProt 상세정보:", len(uniprot))


# --------------------------------------------------
# 4. 필요한 단백질만 연결
# --------------------------------------------------

result = ml_uniprot_ids.to_frame().merge(
    uniprot,
    on="UniProt_ID",
    how="left",
    validate="one_to_one"
)


# --------------------------------------------------
# 5. 연결 상태 확인
# --------------------------------------------------

missing = result["Protein_Name"].isna()

print()
print("===== UniProt 연결 결과 =====")
print("전체:", len(result))
print("연결 성공:", (~missing).sum())
print("연결 실패:", missing.sum())


# --------------------------------------------------
# 6. 결과 저장
# --------------------------------------------------

result.to_csv(
    OUTPUT_FILE,
    index=False,
    encoding="utf-8-sig"
)

print()
print("ML용 UniProt 테이블 생성 완료")
print("저장:", OUTPUT_FILE)