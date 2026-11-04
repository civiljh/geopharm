import pandas as pd
import requests
import time
import os


INPUT_FILE = "data/processed/new_plant_compounds_chembl.csv"
OUTPUT_FILE = "data/processed/new_plant_compounds_chembl_retry.csv"


if not os.path.exists(INPUT_FILE):
    print("ERROR: 입력 파일을 찾을 수 없습니다.")
    print(INPUT_FILE)
    raise SystemExit


df = pd.read_csv(
    INPUT_FILE,
    encoding="utf-8-sig"
)


print()
print("=" * 70)
print("GeoPharm - ChEMBL 오류 데이터 재시도")
print("=" * 70)


# ------------------------------------------------------------
# 재시도 대상
# ------------------------------------------------------------

retry_status = [
    "ERROR_ReadTimeout",
    "HTTP_500"
]

retry_df = df[
    df["ChEMBL_Status"].isin(retry_status)
].copy()


print()
print("전체 화합물:", len(df))
print("재시도 대상:", len(retry_df))


if len(retry_df) == 0:

    print()
    print("재시도할 데이터가 없습니다.")
    df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")
    raise SystemExit


# ------------------------------------------------------------
# ChEMBL 검색
# ------------------------------------------------------------

def search_chembl(inchikey):

    if pd.isna(inchikey):

        return "", "NO_INCHIKEY"

    inchikey = str(inchikey).strip()

    if not inchikey:

        return "", "NO_INCHIKEY"


    url = (
        "https://www.ebi.ac.uk/chembl/api/data/"
        "molecule.json"
    )

    params = {
        "molecule_structures__standard_inchi_key":
            inchikey
    }


    # 같은 화합물이라도 일시적인 서버 문제로
    # 실패할 수 있으므로 최대 3번 시도합니다.

    for attempt in range(1, 4):

        try:

            response = requests.get(
                url,
                params=params,
                timeout=60
            )


            if response.status_code == 200:

                data = response.json()

                molecules = data.get(
                    "molecules",
                    []
                )


                if len(molecules) == 0:

                    return "", "NOT_FOUND"


                molecule = molecules[0]

                chembl_id = molecule.get(
                    "molecule_chembl_id",
                    ""
                )


                if chembl_id:

                    return chembl_id, "OK"

                return "", "NOT_FOUND"


            if response.status_code == 500:

                print(
                    f"    HTTP 500 "
                    f"(재시도 {attempt}/3)"
                )

            else:

                print(
                    f"    HTTP {response.status_code} "
                    f"(재시도 {attempt}/3)"
                )


        except requests.exceptions.ReadTimeout:

            print(
                f"    ReadTimeout "
                f"(재시도 {attempt}/3)"
            )


        except requests.exceptions.RequestException as e:

            print(
                f"    요청 오류: {type(e).__name__} "
                f"(재시도 {attempt}/3)"
            )


        if attempt < 3:

            time.sleep(3)


    return "", "RETRY_FAILED"


# ------------------------------------------------------------
# 재시도
# ------------------------------------------------------------

results = []


for index, row in retry_df.iterrows():

    compound_name = row["Compound_Name"]

    print()
    print(
        f"[{len(results) + 1}/{len(retry_df)}] "
        f"{compound_name}"
    )

    chembl_id, status = search_chembl(
        row["InChIKey"]
    )

    results.append({
        "Original_Index": index,
        "ChEMBL_ID_Retry": chembl_id,
        "ChEMBL_Status_Retry": status
    })

    # ChEMBL 서버에 충분한 간격을 둡니다.
    time.sleep(1)


retry_results = pd.DataFrame(results)


# ------------------------------------------------------------
# 기존 데이터와 재시도 결과 결합
# ------------------------------------------------------------

output_df = df.copy()


for _, row in retry_results.iterrows():

    original_index = row["Original_Index"]

    output_df.loc[
        original_index,
        "ChEMBL_ID"
    ] = row["ChEMBL_ID_Retry"]


    output_df.loc[
        original_index,
        "ChEMBL_Status"
    ] = row["ChEMBL_Status_Retry"]


# ------------------------------------------------------------
# 저장
# ------------------------------------------------------------

output_df.to_csv(
    OUTPUT_FILE,
    index=False,
    encoding="utf-8-sig"
)


# ------------------------------------------------------------
# 결과
# ------------------------------------------------------------

print()
print("=" * 70)
print("ChEMBL 재시도 완료")
print("=" * 70)


print()
print(
    output_df["ChEMBL_Status"]
    .value_counts(dropna=False)
    .to_string()
)


print()
print("저장 파일:")
print(OUTPUT_FILE)


print()
print("완료.")