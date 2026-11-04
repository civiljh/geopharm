import pandas as pd
import requests
import time
import urllib.parse
import os


# ============================================================
# GeoPharm
# 외부 식물 화합물 → PubChem 연결
# ============================================================
#
# external_plant_compounds.csv에 있는 화합물을 PubChem과 연결합니다.
#
# 기존 new_plant_compounds.csv 파일은 건드리지 않습니다.
# ============================================================


INPUT_FILE = "data/raw/external_plant_compounds_linked.csv"
OUTPUT_FILE = "data/raw/external_plant_compounds_pubchem.csv"


# ------------------------------------------------------------
# 입력 파일 확인
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
print("GeoPharm - 외부 식물 화합물 PubChem 연결")
print("=" * 70)

print()
print("입력 화합물:", len(df))


# ------------------------------------------------------------
# PubChem 검색 함수
# ------------------------------------------------------------

def search_pubchem(compound_name):

    if pd.isna(compound_name):

        return {
            "PubChem_CID": "",
            "PubChem_Title": "",
            "PubChem_SMILES": "",
            "InChIKey": "",
            "PubChem_Status": "NO_NAME"
        }

    compound_name = str(
        compound_name
    ).strip()

    if not compound_name:

        return {
            "PubChem_CID": "",
            "PubChem_Title": "",
            "PubChem_SMILES": "",
            "InChIKey": "",
            "PubChem_Status": "NO_NAME"
        }

    encoded_name = urllib.parse.quote(
        compound_name,
        safe=""
    )

    url = (
        "https://pubchem.ncbi.nlm.nih.gov/rest/pug/"
        f"compound/name/{encoded_name}/property/"
        "Title,IsomericSMILES,InChIKey/JSON"
    )

    try:

        response = requests.get(
            url,
            timeout=30
        )

        if response.status_code != 200:

            return {
                "PubChem_CID": "",
                "PubChem_Title": "",
                "PubChem_SMILES": "",
                "InChIKey": "",
                "PubChem_Status":
                    f"HTTP_{response.status_code}"
            }

        data = response.json()

        properties = (
            data
            .get("PropertyTable", {})
            .get("Properties", [])
        )

        if len(properties) == 0:

            return {
                "PubChem_CID": "",
                "PubChem_Title": "",
                "PubChem_SMILES": "",
                "InChIKey": "",
                "PubChem_Status": "NOT_FOUND"
            }

        record = properties[0]

        return {
            "PubChem_CID":
                record.get("CID", ""),

            "PubChem_Title":
                record.get("Title", ""),

            "PubChem_SMILES":
                record.get("SMILES", ""),

            "InChIKey":
                record.get("InChIKey", ""),

            "PubChem_Status":
                "OK"
        }

    except Exception as e:

        return {
            "PubChem_CID": "",
            "PubChem_Title": "",
            "PubChem_SMILES": "",
            "InChIKey": "",
            "PubChem_Status":
                f"ERROR_{type(e).__name__}"
        }


# ------------------------------------------------------------
# 중복 화합물 캐시
# ------------------------------------------------------------

cache = {}

results = []

total = len(df)


# ------------------------------------------------------------
# 전체 화합물 처리
# ------------------------------------------------------------

for index, row in df.iterrows():

    compound_name = row["Compound_Name"]

    print(
        f"[{index + 1}/{total}] {compound_name}"
    )

    if compound_name in cache:

        result = cache[compound_name]

    else:

        result = search_pubchem(
            compound_name
        )

        cache[compound_name] = result

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
    output_df["PubChem_Status"] == "OK"
).sum()

not_found_count = (
    output_df["PubChem_Status"] == "NOT_FOUND"
).sum()

no_inchikey_count = (
    output_df["InChIKey"].astype(str).str.strip() == ""
).sum()

error_count = (
    output_df["PubChem_Status"]
    .astype(str)
    .str.startswith("ERROR")
).sum()


print()
print("=" * 70)
print("PubChem 연결 완료")
print("=" * 70)

print()
print("전체 화합물:", len(output_df))
print("PubChem 연결 성공:", success_count)
print("PubChem 미검색:", not_found_count)
print("InChIKey 없음:", no_inchikey_count)
print("오류:", error_count)


print()
print("식물별 PubChem 연결 결과")

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
        PubChem_Success=(
            "PubChem_Status",
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