import pandas as pd
import requests
from bs4 import BeautifulSoup
import time

# ========================================
# KNApSAcK 식물-화합물 수집 프로그램
# ========================================

INPUT_FILE = "data/raw/medicinal_plants.csv"
OUTPUT_FILE = "data/raw/plant_compounds.csv"


# ----------------------------------------
# 식물 1개의 KNApSAcK 화합물 수집
# ----------------------------------------

def collect_plant(plant_id, scientific_name):

    print()
    print("=" * 60)
    print("식물:", scientific_name)
    print("Plant_ID:", plant_id)
    print("=" * 60)

    url = "https://www.knapsackfamily.com/knapsack_core/result.php"

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

        print("HTTP 상태 코드:", response.status_code)
        print("발견한 표:", len(tables))

        rows = []

        for table in tables:

            for tr in table.find_all("tr"):

                cells = tr.find_all(["th", "td"])

                if len(cells) < 6:
                    continue

                values = [
                    cell.get_text(" ", strip=True)
                    for cell in cells
                ]

                c_id = values[0]

                # KNApSAcK 화합물 ID만 선택
                if not c_id.startswith("C"):
                    continue

                rows.append({
                    "Plant_ID": plant_id,
                    "Scientific_Name": scientific_name,
                    "KNApSAcK_ID": c_id,
                    "CAS": values[1],
                    "Compound_Name": values[2],
                    "Molecular_Formula": values[3],
                    "Molecular_Weight": values[4],
                    "KNApSAcK_Organism": values[5]
                })

        # --------------------------------
        # 중복 제거
        # --------------------------------

        unique_rows = []

        seen = set()

        for row in rows:

            key = (
                row["Plant_ID"],
                row["KNApSAcK_ID"]
            )

            if key not in seen:

                seen.add(key)
                unique_rows.append(row)

        print("수집된 화합물:", len(unique_rows))

        return unique_rows

    except Exception as e:

        print()
        print("오류 발생")
        print("오류 종류:", type(e).__name__)
        print("오류 내용:", str(e))
        print("이 식물은 건너뛰고 다음 식물로 진행합니다.")

        return []


# ========================================
# 식물 목록 읽기
# ========================================

plants = pd.read_csv(
    INPUT_FILE,
    encoding="utf-8-sig"
)

print()
print("=" * 60)
print("KNApSAcK 전체 식물 수집")
print("=" * 60)

print("전체 식물:", len(plants))


# ========================================
# 전체 식물 수집
# ========================================

all_results = []

success_count = 0
empty_count = 0
error_count = 0


for index, row in plants.iterrows():

    plant_id = row["Plant_ID"]
    scientific_name = row["Scientific_Name"]

    print()
    print(
        f"[{index + 1}/{len(plants)}] "
        f"{plant_id} - {scientific_name}"
    )

    try:

        results = collect_plant(
            plant_id,
            scientific_name
        )

        if len(results) > 0:

            all_results.extend(results)
            success_count += 1

        else:

            empty_count += 1

    except Exception:

        error_count += 1

    # 서버에 너무 빠르게 요청하지 않도록 잠시 기다림
    time.sleep(1)


# ========================================
# 전체 결과 DataFrame
# ========================================

result_df = pd.DataFrame(all_results)


# ========================================
# 전체 중복 제거
# ========================================

if len(result_df) > 0:

    result_df = result_df.drop_duplicates(
        subset=[
            "Plant_ID",
            "KNApSAcK_ID"
        ]
    )


# ========================================
# 결과 저장
# ========================================

if len(result_df) > 0:

    result_df.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8-sig"
    )


# ========================================
# 최종 결과
# ========================================

print()
print("=" * 60)
print("KNApSAcK 전체 수집 완료")
print("=" * 60)

print("전체 식물:", len(plants))
print("화합물이 발견된 식물:", success_count)
print("화합물이 발견되지 않은 식물:", empty_count)
print("오류 식물:", error_count)
print("전체 화합물:", len(result_df))

print()
print("저장 파일:")
print(OUTPUT_FILE)


# ========================================
# 식물별 화합물 수
# ========================================

if len(result_df) > 0:

    print()
    print("=" * 60)
    print("식물별 화합물 수")
    print("=" * 60)

    summary = (
        result_df
        .groupby(
            ["Plant_ID", "Scientific_Name"]
        )
        .size()
        .reset_index(
            name="Compound_Count"
        )
    )

    print(
        summary.to_string(index=False)
    )


print()
print("=" * 60)
print("프로그램 종료")
print("=" * 60)