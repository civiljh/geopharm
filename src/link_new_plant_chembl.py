import pandas as pd
import requests
import time
import os


# ============================================================
# GeoPharm
# 새 식물 화합물 → ChEMBL 연결
# ============================================================
#
# new_plant_compounds_pubchem.csv에 있는 화합물만 처리합니다.
#
# 기존 plant_compounds_chembl.csv는 수정하지 않습니다.
# ============================================================


INPUT_FILE = "data/raw/new_plant_compounds_pubchem.csv"
OUTPUT_FILE = "data/processed/new_plant_compounds_chembl.csv"


# ------------------------------------------------------------
# 파일 확인
# ------------------------------------------------------------

if not os.path.exists(INPUT_FILE):

    print()
    print("ERROR: 입력 파일을 찾을 수 없습니다.")
    print(INPUT_FILE)
    raise SystemExit


# ------------------------------------------------------------
# 데이터 읽기
# ------------------------------------------------------------

df = pd.read_csv(
    INPUT_FILE,
    encoding="utf-8-sig"
)

print()
print("=" * 70)
print("GeoPharm - 새 식물 화합물 ChEMBL 연결")
print("=" * 70)

print()
print("입력 화합물:", len(df))


# ------------------------------------------------------------
# ChEMBL 검색 함수
# ------------------------------------------------------------

def search_chembl(inchikey):

    if pd.isna(inchikey):

        return {
            "ChEMBL_ID": "",
            "ChEMBL_Status": "NO_INCHIKEY"
        }

    inchikey = str(
        inchikey
    ).strip()

    if not inchikey:

        return {
            "ChEMBL_ID": "",
            "ChEMBL_Status": "NO_INCHIKEY"
        }

    url = (
        "https://www.ebi.ac.uk/chembl/api/data/"
        "molecule.json"
    )

    params = {
        "molecule_structures__standard_inchi_key":
            inchikey
    }

    try:

        response = requests.get(
            url,
            params=params,
            timeout=30
        )

        if response.status_code != 200:

            return {
                "ChEMBL_ID": "",
                "ChEMBL_Status":
                    f"HTTP_{response.status_code}"
            }

        data = response.json()

        molecules = data.get(
            "molecules",
            []
        )

        if len(molecules) == 0:

            return {
                "ChEMBL_ID": "",
                "ChEMBL_Status": "NOT_FOUND"
            }

        molecule = molecules[0]

        return {
            "ChEMBL_ID":
                molecule.get(
                    "molecule_chembl_id",
                    ""
                ),

            "ChEMBL_Status":
                "OK"
        }

    except Exception as e:

        return {
            "ChEMBL_ID": "",
            "ChEMBL_Status":
                f"ERROR_{type(e).__name__}"
        }


# ------------------------------------------------------------
# 같은 InChIKey는 한 번만 검색
# ------------------------------------------------------------

cache = {}

results = []

total = len(df)


# ------------------------------------------------------------
# ChEMBL 조회
# ------------------------------------------------------------

for index, row in df.iterrows():

    inchikey = row["InChIKey"]

    print(
        f"[{index + 1}/{total}] "
        f"{row['Compound_Name']}"
    )

    if inchikey in cache:

        result = cache[inchikey]

    else:

        result = search_chembl(
            inchikey
        )

        cache[inchikey] = result

        time.sleep(0.2)

    results.append(result)


# ------------------------------------------------------------
# 결과 결합
# ------------------------------------------------------------

result_df = pd.DataFrame(
    results
)

output_df = pd.concat(
    [
        df.reset_index(drop=True),
        result_df.reset_index(drop=True)
    ],
    axis=1
)


# ------------------------------------------------------------
# 저장
# ------------------------------------------------------------

output_df.to_csv(
    OUTPUT_FILE,
    index=False,
    encoding="utf-8-sig"
)


# ------------------------------------------------------------
# 결과 통계
# ------------------------------------------------------------

success_count = (
    output_df["ChEMBL_Status"] == "OK"
).sum()

not_found_count = (
    output_df["ChEMBL_Status"] == "NOT_FOUND"
).sum()

error_count = (
    output_df["ChEMBL_Status"]
    .astype(str)
    .str.startswith("ERROR")
).sum()


print()
print("=" * 70)
print("ChEMBL 연결 완료")
print("=" * 70)

print()
print("전체 화합물:", len(output_df))
print("ChEMBL 연결 성공:", success_count)
print("ChEMBL 미검색:", not_found_count)
print("오류:", error_count)


# ------------------------------------------------------------
# 식물별 결과
# ------------------------------------------------------------

print()
print("식물별 ChEMBL 연결 수:")

summary = (
    output_df
    .groupby(
        [
            "Plant_ID",
            "Common_Name_KO"
        ],
        dropna=False
    )
    .agg(
        Total_Compounds=(
            "Compound_Name",
            "count"
        ),
        ChEMBL_Success=(
            "ChEMBL_Status",
            lambda x: (x == "OK").sum()
        )
    )
    .reset_index()
)

print(
    summary.to_string(
        index=False
    )
)


print()
print("저장 파일:")
print(OUTPUT_FILE)

print()
print("완료.")