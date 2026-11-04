import os
import time
import requests
import pandas as pd


# ============================================================
# GeoPharm - iNaturalist 관찰 데이터 수집
# ============================================================

BASE_URL = "https://api.inaturalist.org/v1/observations"

INPUT_FILE = "data/raw/medicinal_plants.csv"
OUTPUT_FILE = "data/raw/inaturalist_observations.csv"

PER_PAGE = 200
MAX_PAGES = 10


def parse_location(location):
    """
    iNaturalist location 값을
    위도(latitude), 경도(longitude)로 변환한다.

    예:
    "51.1211757176,71.4656294001"
    """

    if not location:
        return None, None

    try:
        parts = str(location).split(",")

        if len(parts) != 2:
            return None, None

        latitude = float(parts[0].strip())
        longitude = float(parts[1].strip())

        if not (-90 <= latitude <= 90):
            return None, None

        if not (-180 <= longitude <= 180):
            return None, None

        return latitude, longitude

    except (TypeError, ValueError):
        return None, None


def fetch_observations(scientific_name):

    all_results = []

    for page in range(1, MAX_PAGES + 1):

        params = {
            "taxon_name": scientific_name,
            "has[]": "geo",
            "quality_grade": "research",
            "per_page": PER_PAGE,
            "page": page
        }

        print(
            f"  iNaturalist 요청: "
            f"{scientific_name} / page {page}"
        )

        response = requests.get(
            BASE_URL,
            params=params,
            timeout=30
        )

        if response.status_code != 200:

            print(
                f"  오류: HTTP {response.status_code}"
            )

            break

        data = response.json()

        results = data.get("results", [])

        if not results:
            break

        for item in results:

            latitude, longitude = parse_location(
                item.get("location")
            )

            taxon = item.get("taxon") or {}

            record = {

                "Scientific_Name":
                    scientific_name,

                "Observation_ID":
                    item.get("id"),

                "Observed_On":
                    item.get("observed_on"),

                "Place_Guess":
                    item.get("place_guess"),

                "Quality_Grade":
                    item.get("quality_grade"),

                "Latitude":
                    latitude,

                "Longitude":
                    longitude,

                "Positional_Accuracy":
                    item.get("positional_accuracy"),

                "Public_Positional_Accuracy":
                    item.get(
                        "public_positional_accuracy"
                    ),

                "Coordinates_Obscured":
                    item.get(
                        "coordinates_obscured"
                    ),

                "Obscured":
                    item.get("obscured"),

                "GeoJSON":
                    str(item.get("geojson"))
                    if item.get("geojson")
                    else None,

                "Taxon_ID":
                    taxon.get("id"),

                "Taxon_Name":
                    taxon.get("name"),

                "Source":
                    "iNaturalist"
            }

            all_results.append(record)

        total_results = data.get(
            "total_results",
            0
        )

        print(
            f"    이번 페이지: {len(results)}건"
            f" / 전체: {total_results}건"
        )

        if len(results) < PER_PAGE:
            break

        if len(all_results) >= total_results:
            break

        time.sleep(1)

    return all_results


def main():

    print("=" * 60)
    print("GeoPharm - iNaturalist 데이터 수집")
    print("=" * 60)

    if not os.path.exists(INPUT_FILE):

        print(
            f"입력 파일이 없습니다: "
            f"{INPUT_FILE}"
        )

        return

    plants = pd.read_csv(INPUT_FILE)

    print(
        f"약용식물 목록: "
        f"{len(plants)}종"
    )

    print()

    all_records = []

    for _, plant in plants.iterrows():

        plant_id = plant["Plant_ID"]

        scientific_name = (
            plant["Scientific_Name"]
        )

        print(
            f"[{plant_id}] "
            f"{scientific_name}"
        )

        records = fetch_observations(
            scientific_name
        )

        for record in records:

            record["Plant_ID"] = plant_id

            record["Common_Name_KO"] = (
                plant.get("Common_Name_KO")
            )

        all_records.extend(records)

        print(
            f"  수집 완료: "
            f"{len(records)}건"
        )

        print()

        time.sleep(1)

    if not all_records:

        print(
            "수집된 데이터가 없습니다."
        )

        return

    df = pd.DataFrame(
        all_records
    )

    # Observation ID 기준 중복 제거
    if "Observation_ID" in df.columns:

        df = df.drop_duplicates(
            subset=["Observation_ID"]
        )

    columns = [

        "Plant_ID",

        "Common_Name_KO",

        "Scientific_Name",

        "Observation_ID",

        "Observed_On",

        "Place_Guess",

        "Quality_Grade",

        "Latitude",

        "Longitude",

        "Positional_Accuracy",

        "Public_Positional_Accuracy",

        "Coordinates_Obscured",

        "Obscured",

        "GeoJSON",

        "Taxon_ID",

        "Taxon_Name",

        "Source"
    ]

    columns = [
        c for c in columns
        if c in df.columns
    ]

    df = df[columns]

    os.makedirs(
        os.path.dirname(
            OUTPUT_FILE
        ),
        exist_ok=True
    )

    df.to_csv(

        OUTPUT_FILE,

        index=False,

        encoding="utf-8-sig"
    )

    print("=" * 60)

    print(
        "수집 완료"
    )

    print("=" * 60)

    print(
        f"총 관찰 데이터: "
        f"{len(df)}건"
    )

    print(
        f"저장 파일: "
        f"{OUTPUT_FILE}"
    )

    coordinate_count = df[
        df["Latitude"].notna()
        & df["Longitude"].notna()
    ].shape[0]

    print()

    print(
        "좌표가 있는 데이터:"
    )

    print(
        f"  {coordinate_count}건"
    )

    print()

    print(
        "식물별 데이터:"
    )

    summary = (

        df.groupby(
            [
                "Plant_ID",
                "Scientific_Name"
            ]
        )

        .agg(

            Observation_Count=(
                "Observation_ID",
                "count"
            ),

            Coordinate_Count=(
                "Latitude",
                "count"
            )
        )

        .reset_index()
    )

    print(
        summary.to_string(
            index=False
        )
    )


if __name__ == "__main__":

    main()