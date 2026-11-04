import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
import os


# ============================================================
# GeoPharm
# 미분석 식물 전용 KNApSAcK 화합물 수집
# ============================================================
#
# new_plants_to_process.csv에 있는 식물만 검색합니다.
#
# 기존 plant_compounds.csv는 수정하지 않습니다.
# ============================================================


INPUT_FILE = "data/processed/new_plants_to_process.csv"
OUTPUT_FILE = "data/raw/new_plant_compounds.csv"


# ------------------------------------------------------------
# 파일 확인
# ------------------------------------------------------------

if not os.path.exists(INPUT_FILE):

    print()
    print("ERROR: 처리 대상 식물 파일을 찾을 수 없습니다.")
    print(INPUT_FILE)
    raise SystemExit


# ------------------------------------------------------------
# 처리 대상 식물 읽기
# ------------------------------------------------------------

plants = pd.read_csv(
    INPUT_FILE,
    encoding="utf-8-sig"
)


print()
print("=" * 70)
print("GeoPharm - 미분석 식물 KNApSAcK 수집")
print("=" * 70)

print()
print("처리 대상 식물:", len(plants))


# ------------------------------------------------------------
# KNApSAcK 검색 함수
# ------------------------------------------------------------

def search_knapsack(
    plant_id,
    common_name_ko,
    scientific_name
):

    print()
    print("=" * 70)
    print("식물 검색")
    print("=" * 70)

    print("Plant_ID:", plant_id)
    print("한국어 이름:", common_name_ko)
    print("학명:", scientific_name)

    url = (
        "https://www.knapsackfamily.com/"
        "knapsack_core/result.php"
    )

    params = {
        "sname": "organism",
        "word": scientific_name
    }

    try:

        response = requests.get(
            url,
            params=params,
            timeout=30
        )

        response.raise_for_status()

        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )

        tables = soup.find_all("table")

        print("HTTP status:", response.status_code)
        print("Tables found:", len(tables))

        rows = []

        for table in tables:

            for tr in table.find_all("tr"):

                cells = tr.find_all(
                    ["th", "td"]
                )

                if len(cells) < 6:
                    continue

                values = [
                    cell.get_text(
                        " ",
                        strip=True
                    )
                    for cell in cells
                ]

                knapsack_id = values[0]

                if not knapsack_id.startswith("C"):
                    continue

                rows.append({

                    "Plant_ID": plant_id,

                    "Common_Name_KO":
                        common_name_ko,

                    "Scientific_Name":
                        scientific_name,

                    "KNApSAcK_ID":
                        knapsack_id,

                    "CAS":
                        values[1],

                    "Compound_Name":
                        values[2],

                    "Molecular_Formula":
                        values[3],

                    "Molecular_Weight":
                        values[4],

                    "KNApSAcK_Organism":
                        values[5]
                })

        result_df = pd.DataFrame(rows)

        if len(result_df) > 0:

            result_df = result_df.drop_duplicates(
                subset=[
                    "Plant_ID",
                    "KNApSAcK_ID"
                ]
            )

        print()
        print("화합물 수:", len(result_df))

        return result_df

    except Exception as e:

        print()
        print("검색 오류")
        print("오류 종류:", type(e).__name__)
        print("오류 내용:", str(e))

        return pd.DataFrame()


# ------------------------------------------------------------
# 전체 미분석 식물 처리
# ------------------------------------------------------------

all_results = []


for index, row in plants.iterrows():

    plant_id = str(
        row["Plant_ID"]
    ).strip()

    common_name_ko = str(
        row["Common_Name_KO"]
    ).strip()

    scientific_name = str(
        row["Scientific_Name"]
    ).strip()

    result = search_knapsack(
        plant_id,
        common_name_ko,
        scientific_name
    )

    if len(result) > 0:

        all_results.append(result)

    # 서버에 너무 빠르게 요청하지 않도록 대기
    time.sleep(1)


# ------------------------------------------------------------
# 결과 합치기
# ------------------------------------------------------------

if len(all_results) > 0:

    output_df = pd.concat(
        all_results,
        ignore_index=True
    )

else:

    output_df = pd.DataFrame(
        columns=[
            "Plant_ID",
            "Common_Name_KO",
            "Scientific_Name",
            "KNApSAcK_ID",
            "CAS",
            "Compound_Name",
            "Molecular_Formula",
            "Molecular_Weight",
            "KNApSAcK_Organism"
        ]
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
# 최종 결과
# ------------------------------------------------------------

print()
print("=" * 70)
print("미분석 식물 KNApSAcK 수집 완료")
print("=" * 70)

print()
print("처리 대상 식물:", len(plants))
print("수집된 화합물:", len(output_df))

print()
print("식물별 화합물 수:")

if len(output_df) > 0:

    summary = (
        output_df
        .groupby(
            [
                "Plant_ID",
                "Common_Name_KO",
                "Scientific_Name"
            ]
        )
        .size()
        .reset_index(
            name="Compound_Count"
        )
    )

    print(
        summary.to_string(
            index=False
        )
    )

else:

    print("수집된 화합물이 없습니다.")


print()
print("저장 파일:")
print(OUTPUT_FILE)

print()
print("완료.")