import os
import time
import requests
import pandas as pd


# ============================================================
# GeoPharm
# 새 약용식물 GBIF + iNaturalist 분포 자동 수집
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)


PLANT_FILE = os.path.join(
    BASE_DIR,
    "data",
    "raw",
    "medicinal_plants.csv"
)


DISTRIBUTION_FILE = os.path.join(
    BASE_DIR,
    "data",
    "processed",
    "plant_distribution.csv"
)


STATUS_FILE = os.path.join(
    BASE_DIR,
    "data",
    "processed",
    "distribution_collection_status.csv"
)


# ============================================================
# API
# ============================================================

GBIF_SPECIES_MATCH_URL = (
    "https://api.gbif.org/v1/species/match"
)

GBIF_OCCURRENCE_URL = (
    "https://api.gbif.org/v1/occurrence/search"
)

INATURALIST_URL = (
    "https://api.inaturalist.org/v1/observations"
)


# ============================================================
# 수집 설정
# ============================================================

GBIF_PER_PAGE = 300
GBIF_MAX_PAGES = 10

INAT_PER_PAGE = 200
INAT_MAX_PAGES = 10

REQUEST_TIMEOUT = 30

SLEEP_SECONDS = 1


# ============================================================
# 공통 컬럼
# ============================================================

DISTRIBUTION_COLUMNS = [

    "Plant_ID",

    "Common_Name_KO",

    "Scientific_Name",

    "Source",

    "Source_Record_ID",

    "Latitude",

    "Longitude",

    "Country",

    "Country_Code",

    "Place",

    "Quality_Grade",

    "Positional_Accuracy",

    "Coordinates_Obscured",

    "Basis_Of_Record",

    "Event_Date",

    "Source_URL"
]


STATUS_COLUMNS = [

    "Plant_ID",

    "Scientific_Name",

    "GBIF_Count",

    "iNaturalist_Count",

    "Total_Count",

    "Status",

    "Processed_At"
]


# ============================================================
# 안전한 값 변환
# ============================================================

def clean_value(value):

    if value is None:
        return None

    try:

        if pd.isna(value):
            return None

    except Exception:

        pass

    return value


# ============================================================
# GBIF
# ============================================================

def gbif_match_species(
    scientific_name
):

    params = {
        "name": scientific_name
    }

    try:

        response = requests.get(
            GBIF_SPECIES_MATCH_URL,
            params=params,
            timeout=REQUEST_TIMEOUT
        )

    except Exception as e:

        print(
            f"  GBIF species match 오류: {e}"
        )

        return None

    if response.status_code != 200:

        print(
            "  GBIF species match 오류: "
            f"HTTP {response.status_code}"
        )

        return None

    data = response.json()

    usage_key = data.get(
        "usageKey"
    )

    matched_name = data.get(
        "scientificName"
    )

    match_type = data.get(
        "matchType"
    )

    rank = data.get(
        "rank"
    )

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


def fetch_gbif(
    plant_id,
    common_name_ko,
    scientific_name
):

    records = []

    print(
        "  [GBIF] 식물명 매칭 중..."
    )

    taxon_key = gbif_match_species(
        scientific_name
    )

    if taxon_key is None:

        return records

    for page in range(
        1,
        GBIF_MAX_PAGES + 1
    ):

        offset = (
            (page - 1)
            * GBIF_PER_PAGE
        )

        params = {

            "taxonKey":
                taxon_key,

            "hasCoordinate":
                "true",

            "limit":
                GBIF_PER_PAGE,

            "offset":
                offset
        }

        print(
            f"  [GBIF] page {page}"
        )

        try:

            response = requests.get(
                GBIF_OCCURRENCE_URL,
                params=params,
                timeout=REQUEST_TIMEOUT
            )

        except Exception as e:

            print(
                f"  GBIF 요청 오류: {e}"
            )

            break

        if response.status_code != 200:

            print(
                "  GBIF 오류: "
                f"HTTP {response.status_code}"
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

            record_id = item.get(
                "key"
            )

            record = {

                "Plant_ID":
                    plant_id,

                "Common_Name_KO":
                    common_name_ko,

                "Scientific_Name":
                    scientific_name,

                "Source":
                    "GBIF",

                "Source_Record_ID":
                    record_id,

                "Latitude":
                    latitude,

                "Longitude":
                    longitude,

                "Country":
                    item.get(
                        "country"
                    ),

                "Country_Code":
                    item.get(
                        "countryCode"
                    ),

                "Place":
                    item.get(
                        "locality"
                    )
                    or
                    item.get(
                        "stateProvince"
                    ),

                "Quality_Grade":
                    None,

                "Positional_Accuracy":
                    item.get(
                        "coordinateUncertaintyInMeters"
                    ),

                "Coordinates_Obscured":
                    None,

                "Basis_Of_Record":
                    item.get(
                        "basisOfRecord"
                    ),

                "Event_Date":
                    item.get(
                        "eventDate"
                    ),

                "Source_URL":
                    (
                        "https://www.gbif.org/"
                        "occurrence/"
                        f"{record_id}"
                    )
            }

            records.append(
                record
            )

        print(
            f"    이번 페이지: "
            f"{len(results)}건 / "
            f"전체: {total_count}건"
        )

        if len(results) < GBIF_PER_PAGE:

            break

        if (
            offset + len(results)
            >= total_count
        ):

            break

        time.sleep(
            SLEEP_SECONDS
        )

    return records


# ============================================================
# iNaturalist
# ============================================================

def parse_location(
    location
):

    if not location:

        return None, None

    try:

        parts = str(
            location
        ).split(",")

        if len(parts) != 2:

            return None, None

        latitude = float(
            parts[0].strip()
        )

        longitude = float(
            parts[1].strip()
        )

        if not (
            -90
            <= latitude
            <= 90
        ):

            return None, None

        if not (
            -180
            <= longitude
            <= 180
        ):

            return None, None

        return (
            latitude,
            longitude
        )

    except (
        TypeError,
        ValueError
    ):

        return None, None


def fetch_inaturalist(
    plant_id,
    common_name_ko,
    scientific_name
):

    records = []

    for page in range(
        1,
        INAT_MAX_PAGES + 1
    ):

        params = {

            "taxon_name":
                scientific_name,

            "has[]":
                "geo",

            "quality_grade":
                "research",

            "per_page":
                INAT_PER_PAGE,

            "page":
                page
        }

        print(
            f"  [iNaturalist] "
            f"page {page}"
        )

        try:

            response = requests.get(
                INATURALIST_URL,
                params=params,
                timeout=REQUEST_TIMEOUT
            )

        except Exception as e:

            print(
                f"  iNaturalist 요청 오류: {e}"
            )

            break

        if response.status_code != 200:

            print(
                "  iNaturalist 오류: "
                f"HTTP {response.status_code}"
            )

            break

        data = response.json()

        results = data.get(
            "results",
            []
        )

        total_results = data.get(
            "total_results",
            0
        )

        if not results:

            break

        for item in results:

            latitude, longitude = (
                parse_location(
                    item.get(
                        "location"
                    )
                )
            )

            if (
                latitude is None
                or longitude is None
            ):

                continue

            observation_id = item.get(
                "id"
            )

            taxon = (
                item.get("taxon")
                or {}
            )

            record = {

                "Plant_ID":
                    plant_id,

                "Common_Name_KO":
                    common_name_ko,

                "Scientific_Name":
                    scientific_name,

                "Source":
                    "iNaturalist",

                "Source_Record_ID":
                    observation_id,

                "Latitude":
                    latitude,

                "Longitude":
                    longitude,

                "Country":
                    None,

                "Country_Code":
                    None,

                "Place":
                    item.get(
                        "place_guess"
                    ),

                "Quality_Grade":
                    item.get(
                        "quality_grade"
                    ),

                "Positional_Accuracy":
                    item.get(
                        "positional_accuracy"
                    ),

                "Coordinates_Obscured":
                    item.get(
                        "coordinates_obscured"
                    ),

                "Basis_Of_Record":
                    "HUMAN_OBSERVATION",

                "Event_Date":
                    item.get(
                        "observed_on"
                    ),

                "Source_URL":
                    (
                        "https://www.inaturalist.org/"
                        "observations/"
                        f"{observation_id}"
                    )
            }

            records.append(
                record
            )

        print(
            f"    이번 페이지: "
            f"{len(results)}건 / "
            f"전체: {total_results}건"
        )

        if len(results) < INAT_PER_PAGE:

            break

        if (
            page * INAT_PER_PAGE
            >= total_results
        ):

            break

        time.sleep(
            SLEEP_SECONDS
        )

    return records


# ============================================================
# 기존 분포 데이터 읽기
# ============================================================

def load_distribution():

    if not os.path.exists(
        DISTRIBUTION_FILE
    ):

        return pd.DataFrame(
            columns=DISTRIBUTION_COLUMNS
        )

    try:

        df = pd.read_csv(
            DISTRIBUTION_FILE,
            encoding="utf-8-sig"
        )

    except Exception:

        df = pd.read_csv(
            DISTRIBUTION_FILE,
            encoding="utf-8"
        )

    for column in DISTRIBUTION_COLUMNS:

        if column not in df.columns:

            df[column] = None

    return df[
        DISTRIBUTION_COLUMNS
    ]


# ============================================================
# 처리 상태 읽기
# ============================================================

def load_status():

    if not os.path.exists(
        STATUS_FILE
    ):

        return pd.DataFrame(
            columns=STATUS_COLUMNS
        )

    try:

        df = pd.read_csv(
            STATUS_FILE,
            encoding="utf-8-sig"
        )

    except Exception:

        df = pd.read_csv(
            STATUS_FILE,
            encoding="utf-8"
        )

    for column in STATUS_COLUMNS:

        if column not in df.columns:

            df[column] = None

    return df[
        STATUS_COLUMNS
    ]


# ============================================================
# 처리 상태 저장
# ============================================================

def save_status(
    status_df
):

    os.makedirs(
        os.path.dirname(
            STATUS_FILE
        ),
        exist_ok=True
    )

    status_df.to_csv(
        STATUS_FILE,
        index=False,
        encoding="utf-8-sig"
    )


# ============================================================
# 식물별 수집
# ============================================================

def collect_plant(
    plant
):

    plant_id = str(
        plant.get(
            "Plant_ID",
            ""
        )
    ).strip()

    common_name_ko = clean_value(
        plant.get(
            "Common_Name_KO"
        )
    )

    scientific_name = str(
        plant.get(
            "Scientific_Name",
            ""
        )
    ).strip()

    print()
    print("=" * 60)
    print(
        f"[{plant_id}] "
        f"{common_name_ko} / "
        f"{scientific_name}"
    )
    print("=" * 60)

    gbif_records = fetch_gbif(
        plant_id,
        common_name_ko,
        scientific_name
    )

    print(
        f"  GBIF 수집: "
        f"{len(gbif_records)}건"
    )

    time.sleep(
        SLEEP_SECONDS
    )

    inat_records = fetch_inaturalist(
        plant_id,
        common_name_ko,
        scientific_name
    )

    print(
        f"  iNaturalist 수집: "
        f"{len(inat_records)}건"
    )

    records = (
        gbif_records
        + inat_records
    )

    return records


# ============================================================
# 메인
# ============================================================

def main():

    print("=" * 60)
    print(
        "GeoPharm - 새 약용식물 "
        "GBIF + iNaturalist 자동 분포 수집"
    )
    print("=" * 60)

    if not os.path.exists(
        PLANT_FILE
    ):

        print(
            "식물 목록 파일이 없습니다:"
        )

        print(
            PLANT_FILE
        )

        return

    plants = pd.read_csv(
        PLANT_FILE,
        encoding="utf-8-sig"
    )

    distribution_df = load_distribution()

    status_df = load_status()

    print(
        f"전체 약용식물: "
        f"{len(plants)}종"
    )

    existing_distribution_ids = set()

    if (
        not distribution_df.empty
        and "Plant_ID"
        in distribution_df.columns
    ):

        existing_distribution_ids = set(
            distribution_df[
                "Plant_ID"
            ]
            .dropna()
            .astype(str)
        )

    processed_status_ids = set()

    if (
        not status_df.empty
        and "Plant_ID"
        in status_df.columns
    ):

        processed_status_ids = set(
            status_df[
                "Plant_ID"
            ]
            .dropna()
            .astype(str)
        )

    # --------------------------------------------------------
    # 새 식물 찾기
    # --------------------------------------------------------

    new_plants = []

    for _, plant in plants.iterrows():

        plant_id = str(
            plant.get(
                "Plant_ID",
                ""
            )
        ).strip()

        if not plant_id:

            continue

        # 이미 분포 데이터가 있는 식물
        if plant_id in existing_distribution_ids:

            continue

        # 이미 처리 상태가 기록된 식물
        if plant_id in processed_status_ids:

            continue

        new_plants.append(
            plant
        )

    print(
        f"새로 처리할 식물: "
        f"{len(new_plants)}종"
    )

    if not new_plants:

        print()
        print(
            "새로 처리할 식물이 없습니다."
        )

        print(
            "현재 분포 데이터는 최신 상태입니다."
        )

        return

    # --------------------------------------------------------
    # 새 식물 처리
    # --------------------------------------------------------

    all_new_records = []

    for plant in new_plants:

        plant_id = str(
            plant.get(
                "Plant_ID",
                ""
            )
        ).strip()

        scientific_name = str(
            plant.get(
                "Scientific_Name",
                ""
            )
        ).strip()

        if not scientific_name:

            print(
                f"[{plant_id}] "
                "학명이 없어 건너뜁니다."
            )

            continue

        records = collect_plant(
            plant
        )

        all_new_records.extend(
            records
        )

        # ----------------------------------------------------
        # 처리 상태 기록
        # ----------------------------------------------------

        gbif_count = sum(
            1
            for record in records
            if record.get(
                "Source"
            ) == "GBIF"
        )

        inat_count = sum(
            1
            for record in records
            if record.get(
                "Source"
            ) == "iNaturalist"
        )

        total_count = len(
            records
        )

        if total_count > 0:

            status = "SUCCESS"

        else:

            status = "NO_DATA"

        status_record = {

            "Plant_ID":
                plant_id,

            "Scientific_Name":
                scientific_name,

            "GBIF_Count":
                gbif_count,

            "iNaturalist_Count":
                inat_count,

            "Total_Count":
                total_count,

            "Status":
                status,

            "Processed_At":
                pd.Timestamp.now().isoformat()
        }

        status_df = pd.concat(
            [
                status_df,
                pd.DataFrame(
                    [status_record]
                )
            ],
            ignore_index=True
        )

        save_status(
            status_df
        )

        time.sleep(
            SLEEP_SECONDS
        )

    # --------------------------------------------------------
    # 새 데이터가 없는 경우
    # --------------------------------------------------------

    if not all_new_records:

        print()
        print(
            "새로운 분포 관찰 데이터가 없습니다."
        )

        print(
            f"처리 상태 파일: "
            f"{STATUS_FILE}"
        )

        return

    # --------------------------------------------------------
    # 새 데이터 DataFrame
    # --------------------------------------------------------

    new_df = pd.DataFrame(
        all_new_records
    )

    for column in DISTRIBUTION_COLUMNS:

        if column not in new_df.columns:

            new_df[column] = None

    new_df = new_df[
        DISTRIBUTION_COLUMNS
    ]

    # --------------------------------------------------------
    # 기존 데이터 + 새 데이터
    # --------------------------------------------------------

    combined_df = pd.concat(
        [
            distribution_df,
            new_df
        ],
        ignore_index=True
    )

    # --------------------------------------------------------
    # Source + Source_Record_ID 기준 중복 제거
    # --------------------------------------------------------

    if (
        "Source"
        in combined_df.columns
        and
        "Source_Record_ID"
        in combined_df.columns
    ):

        combined_df = (
            combined_df
            .drop_duplicates(
                subset=[
                    "Source",
                    "Source_Record_ID"
                ]
            )
        )

    # --------------------------------------------------------
    # 좌표가 없는 데이터 제거
    # --------------------------------------------------------

    combined_df = combined_df[
        combined_df[
            "Latitude"
        ].notna()
        &
        combined_df[
            "Longitude"
        ].notna()
    ]

    # --------------------------------------------------------
    # 저장
    # --------------------------------------------------------

    os.makedirs(
        os.path.dirname(
            DISTRIBUTION_FILE
        ),
        exist_ok=True
    )

    combined_df.to_csv(
        DISTRIBUTION_FILE,
        index=False,
        encoding="utf-8-sig"
    )

    # --------------------------------------------------------
    # 결과
    # --------------------------------------------------------

    print()
    print("=" * 60)
    print(
        "분포 데이터 자동 수집 완료"
    )
    print("=" * 60)

    print(
        f"이번에 추가된 원본 기록: "
        f"{len(new_df)}건"
    )

    print(
        f"현재 전체 분포 기록: "
        f"{len(combined_df)}건"
    )

    print(
        f"저장 파일:"
    )

    print(
        DISTRIBUTION_FILE
    )

    print()
    print(
        "이번 수집 식물별 결과:"
    )

    summary = (
        new_df
        .groupby(
            [
                "Plant_ID",
                "Common_Name_KO",
                "Scientific_Name",
                "Source"
            ]
        )
        .agg(
            Observation_Count=(
                "Source_Record_ID",
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

    print()
    print(
        "처리 상태 파일:"
    )

    print(
        STATUS_FILE
    )


if __name__ == "__main__":

    main()