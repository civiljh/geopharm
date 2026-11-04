import os
import time
import requests
import pandas as pd


# ============================================================
# GeoPharm - GBIF 관찰 데이터 수집
# ============================================================

SPECIES_MATCH_URL = "https://api.gbif.org/v1/species/match"
OCCURRENCE_URL = "https://api.gbif.org/v1/occurrence/search"

INPUT_FILE = "data/raw/medicinal_plants.csv"
OUTPUT_FILE = "data/raw/gbif_observations.csv"

PER_PAGE = 300
MAX_PAGES = 4


def match_species(scientific_name):

    params = {
        "name": scientific_name
    }

    response = requests.get(
        SPECIES_MATCH_URL,
        params=params,
        timeout=30
    )

    if response.status_code != 200:
        print(
            f"  Species Match 오류: "
            f"HTTP {response.status_code}"
        )
        return None

    data = response.json()

    usage_key = data.get("usageKey")
    match_type = data.get("matchType")
    rank = data.get("rank")
    matched_name = data.get("scientificName")

    print(
        f"  GBIF 매칭: {matched_name}"
    )

    print(
        f"  taxonKey: {usage_key}"
    )

    print(
        f"  matchType: {match_type}"
    )

    print(
        f"  rank: {rank}"
    )

    return usage_key


def fetch_occurrences(
    scientific_name,
    taxon_key
):

    records = []

    for page in range(1, MAX_PAGES + 1):

        offset = (
            (page - 1)
            * PER_PAGE
        )

        params = {

            "taxonKey":
                taxon_key,

            "hasCoordinate":
                "true",

            "limit":
                PER_PAGE,

            "offset":
                offset
        }

        print(
            f"  GBIF 관찰 요청: "
            f"page {page}"
        )

        response = requests.get(
            OCCURRENCE_URL,
            params=params,
            timeout=30
        )

        if response.status_code != 200:

            print(
                f"  오류: HTTP "
                f"{response.status_code}"
            )

            break

        data = response.json()

        results = data.get(
            "results",
            []
        )

        total_count = data.get(
            "count",
            0
        )

        if not results:
            break

        for item in results:

            latitude = item.get(
                "decimalLatitude"
            )

            longitude = item.get(
                "decimalLongitude"
            )

            if (
                latitude is None
                or longitude is None
            ):
                continue

            record = {

                "Scientific_Name":
                    scientific_name,

                "GBIF_ID":
                    item.get("key"),

                "GBIF_Taxon_Key":
                    taxon_key,

                "Species":
                    item.get("species"),

                "Scientific_Name_GBIF":
                    item.get(
                        "scientificName"
                    ),

                "Latitude":
                    latitude,

                "Longitude":
                    longitude,

                "Country":
                    item.get("country"),

                "Country_Code":
                    item.get(
                        "countryCode"
                    ),

                "Locality":
                    item.get(
                        "locality"
                    ),

                "State_Province":
                    item.get(
                        "stateProvince"
                    ),

                "County":
                    item.get("county"),

                "Basis_Of_Record":
                    item.get(
                        "basisOfRecord"
                    ),

                "Occurrence_Status":
                    item.get(
                        "occurrenceStatus"
                    ),

                "Event_Date":
                    item.get(
                        "eventDate"
                    ),

                "Dataset_Name":
                    item.get(
                        "datasetName"
                    ),

                "Publisher":
                    item.get(
                        "publishingOrgKey"
                    ),

                "Source":
                    "GBIF"
            }

            records.append(record)

        print(
            f"    이번 페이지: "
            f"{len(results)}건"
            f" / 전체: "
            f"{total_count}건"
        )

        if len(results) < PER_PAGE:
            break

        if len(records) >= total_count:
            break

        time.sleep(1)

    return records


def main():

    print("=" * 60)
    print(
        "GeoPharm - GBIF 데이터 수집"
    )
    print("=" * 60)

    if not os.path.exists(
        INPUT_FILE
    ):

        print(
            f"입력 파일이 없습니다: "
            f"{INPUT_FILE}"
        )

        return

    plants = pd.read_csv(
        INPUT_FILE
    )

    print(
        f"약용식물 목록: "
        f"{len(plants)}종"
    )

    print()

    all_records = []

    for _, plant in plants.iterrows():

        plant_id = plant[
            "Plant_ID"
        ]

        scientific_name = plant[
            "Scientific_Name"
        ]

        print(
            f"[{plant_id}] "
            f"{scientific_name}"
        )

        taxon_key = match_species(
            scientific_name
        )

        if taxon_key is None:

            print(
                "  taxonKey를 찾지 못했습니다."
            )

            print()

            continue

        records = fetch_occurrences(
            scientific_name,
            taxon_key
        )

        for record in records:

            record[
                "Plant_ID"
            ] = plant_id

            record[
                "Common_Name_KO"
            ] = plant.get(
                "Common_Name_KO"
            )

        all_records.extend(
            records
        )

        print(
            f"  수집 완료: "
            f"{len(records)}건"
        )

        print()

        time.sleep(1)

    if not all_records:

        print(
            "수집된 GBIF 데이터가 없습니다."
        )

        return

    df = pd.DataFrame(
        all_records
    )

    if "GBIF_ID" in df.columns:

        df = df.drop_duplicates(
            subset=["GBIF_ID"]
        )

    columns = [

        "Plant_ID",

        "Common_Name_KO",

        "Scientific_Name",

        "GBIF_ID",

        "GBIF_Taxon_Key",

        "Species",

        "Scientific_Name_GBIF",

        "Latitude",

        "Longitude",

        "Country",

        "Country_Code",

        "Locality",

        "State_Province",

        "County",

        "Basis_Of_Record",

        "Occurrence_Status",

        "Event_Date",

        "Dataset_Name",

        "Publisher",

        "Source"
    ]

    columns = [
        c
        for c in columns
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
        f"총 GBIF 관찰 데이터: "
        f"{len(df)}건"
    )

    print(
        f"저장 파일: "
        f"{OUTPUT_FILE}"
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
                "GBIF_ID",
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