import pandas as pd


INPUT_FILE = "data/raw/plant_compounds_with_inchikey.csv"
OUTPUT_FILE = "data/processed/plant_compounds_final.csv"


df = pd.read_csv(INPUT_FILE)


# 최종 공통 화학물질 식별자 생성
# 1순위: PubChem InChIKey
# 2순위: KNApSAcK SMILES에서 RDKit으로 생성한 InChIKey

df["Chemical_InChIKey"] = df["InChIKey"]

df["Chemical_InChIKey"] = (
    df["Chemical_InChIKey"]
    .fillna(df["KNApSAcK_InChIKey"])
)


print("================================")
print("최종 화학물질 식별자 생성")
print("================================")

print("전체 성분:", len(df))

print(
    "Chemical_InChIKey 확보:",
    df["Chemical_InChIKey"].notna().sum()
)

print(
    "Chemical_InChIKey 미확보:",
    df["Chemical_InChIKey"].isna().sum()
)

print()

# 출처별 확인
print("PubChem InChIKey 사용:", df["InChIKey"].notna().sum())
print(
    "KNApSAcK/RDKit InChIKey 사용:",
    (
        df["InChIKey"].isna()
        & df["KNApSAcK_InChIKey"].notna()
    ).sum()
)

print()

# 최종 키가 없는 행 확인
missing = df[df["Chemical_InChIKey"].isna()]

print(
    "최종 InChIKey 미확보 성분:",
    len(missing)
)

if len(missing) > 0:

    print()

    print(
        missing[
            [
                "KNApSAcK_ID",
                "Compound_Name",
                "CAS",
                "PubChem_Status",
            ]
        ].to_string(index=False)
    )


# 최종 데이터 저장
df.to_csv(
    OUTPUT_FILE,
    index=False,
    encoding="utf-8-sig"
)


print()
print("================================")
print("최종 파일 저장 완료")
print("================================")
print("파일:", OUTPUT_FILE)