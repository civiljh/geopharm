import os
import pandas as pd

INAT_FILE = "data/raw/inaturalist_observations.csv"
GBIF_FILE = "data/raw/gbif_observations.csv"

OUT_FILE = "data/processed/plant_distribution.csv"
SUMMARY_FILE = "data/processed/plant_distribution_summary.csv"


def check_file(path):
    if not os.path.exists(path):
        raise FileNotFoundError(f"파일을 찾을 수 없습니다: {path}")


def valid_coordinates(df):
    lat = pd.to_numeric(df["Latitude"], errors="coerce")
    lon = pd.to_numeric(df["Longitude"], errors="coerce")

    return (
        lat.notna()
        & lon.notna()
        & lat.between(-90, 90)
        & lon.between(-180, 180)
        & ~((lat == 0) & (lon == 0))
    )


print("=" * 70)
print("GeoPharm 약용식물 분포 데이터 통합")
print("=" * 70)

check_file(INAT_FILE)
check_file(GBIF_FILE)

print("\n[1] iNaturalist 데이터 읽는 중...")
inat = pd.read_csv(INAT_FILE)

print(f"iNaturalist 원본 행 수: {len(inat):,}")

print("\n[2] GBIF 데이터 읽는 중...")
gbif = pd.read_csv(GBIF_FILE)

print(f"GBIF 원본 행 수: {len(gbif):,}")


# ---------------------------------------------------------
# iNaturalist 표준화
# ---------------------------------------------------------

print("\n[3] iNaturalist 데이터 표준화...")

inat_std = pd.DataFrame({
    "Plant_ID": inat.get("Plant_ID"),
    "Common_Name_KO": inat.get("Common_Name_KO"),
    "Scientific_Name": inat.get("Scientific_Name"),
    "Source": "iNaturalist",
    "Source_Record_ID": inat.get("Observation_ID"),
    "Latitude": inat.get("Latitude"),
    "Longitude": inat.get("Longitude"),
    "Country": "",
    "Country_Code": "",
    "Place": inat.get("Place_Guess"),
    "Quality_Grade": inat.get("Quality_Grade"),
    "Positional_Accuracy": inat.get("Positional_Accuracy"),
    "Coordinates_Obscured": inat.get("Coordinates_Obscured"),
    "Basis_Of_Record": "OBSERVATION",
    "Event_Date": inat.get("Observed_On"),
    "Source_URL": "",
})


# iNaturalist 관찰 페이지 주소
inat_std["Source_URL"] = (
    "https://www.inaturalist.org/observations/"
    + inat_std["Source_Record_ID"].astype(str)
)


# ---------------------------------------------------------
# GBIF 표준화
# ---------------------------------------------------------

print("[4] GBIF 데이터 표준화...")

gbif_std = pd.DataFrame({
    "Plant_ID": gbif.get("Plant_ID"),
    "Common_Name_KO": "",
    "Scientific_Name": gbif.get("Scientific_Name"),
    "Source": "GBIF",
    "Source_Record_ID": gbif.get("GBIF_ID"),
    "Latitude": gbif.get("Latitude"),
    "Longitude": gbif.get("Longitude"),
    "Country": gbif.get("Country"),
    "Country_Code": gbif.get("Country_Code"),
    "Place": gbif.get("Locality"),
    "Quality_Grade": "",
    "Positional_Accuracy": "",
    "Coordinates_Obscured": "",
    "Basis_Of_Record": gbif.get("Basis_Of_Record"),
    "Event_Date": gbif.get("Event_Date"),
    "Source_URL": "",
})


# GBIF 관찰 페이지 주소
gbif_std["Source_URL"] = (
    "https://www.gbif.org/occurrence/"
    + gbif_std["Source_Record_ID"].astype(str)
)


# ---------------------------------------------------------
# 두 데이터 합치기
# ---------------------------------------------------------

print("[5] iNaturalist + GBIF 데이터 합치는 중...")

distribution = pd.concat(
    [inat_std, gbif_std],
    ignore_index=True
)


# ---------------------------------------------------------
# 좌표 숫자 변환
# ---------------------------------------------------------

print("[6] 좌표 데이터 검사...")

distribution["Latitude"] = pd.to_numeric(
    distribution["Latitude"],
    errors="coerce"
)

distribution["Longitude"] = pd.to_numeric(
    distribution["Longitude"],
    errors="coerce"
)


before_count = len(distribution)

valid_mask = valid_coordinates(distribution)

distribution = distribution.loc[valid_mask].copy()

invalid_count = before_count - len(distribution)


# ---------------------------------------------------------
# 중복 Source Record 제거
# ---------------------------------------------------------

print("[7] 동일한 원본 기록 중복 제거...")

before_duplicate = len(distribution)

distribution = distribution.drop_duplicates(
    subset=["Source", "Source_Record_ID"]
)

duplicate_count = before_duplicate - len(distribution)


# ---------------------------------------------------------
# 정렬
# ---------------------------------------------------------

distribution = distribution.sort_values(
    by=[
        "Plant_ID",
        "Scientific_Name",
        "Source",
        "Source_Record_ID"
    ],
    na_position="last"
).reset_index(drop=True)


# ---------------------------------------------------------
# 저장
# ---------------------------------------------------------

os.makedirs("data/processed", exist_ok=True)

distribution.to_csv(
    OUT_FILE,
    index=False,
    encoding="utf-8-sig"
)


# ---------------------------------------------------------
# 식물별 / 출처별 요약
# ---------------------------------------------------------

summary = (
    distribution
    .groupby(
        [
            "Plant_ID",
            "Scientific_Name",
            "Source"
        ],
        dropna=False
    )
    .agg(
        Observation_Count=("Source_Record_ID", "count"),
        Coordinate_Count=("Latitude", "count"),
        Unique_Coordinate_Count=(
            "Source_Record_ID",
            "nunique"
        )
    )
    .reset_index()
)

summary.to_csv(
    SUMMARY_FILE,
    index=False,
    encoding="utf-8-sig"
)


# ---------------------------------------------------------
# 결과 출력
# ---------------------------------------------------------

print("\n" + "=" * 70)
print("완료!")
print("=" * 70)

print(f"\n통합 데이터:")
print(f"  {OUT_FILE}")

print(f"\n요약 데이터:")
print(f"  {SUMMARY_FILE}")

print("\n전체 통합 관찰 수:")
print(f"  {len(distribution):,}")

print("\n좌표 오류로 제외된 행:")
print(f"  {invalid_count:,}")

print("\n중복 제거된 행:")
print(f"  {duplicate_count:,}")

print("\n출처별 데이터:")
print(
    distribution["Source"]
    .value_counts()
    .to_string()
)

print("\n식물별 데이터:")
plant_summary = (
    distribution
    .groupby(
        ["Plant_ID", "Scientific_Name"],
        dropna=False
    )
    .size()
    .reset_index(name="Count")
)

print(plant_summary.to_string(index=False))

print("\n" + "=" * 70)
print("다음 단계에서 이 파일을 지도에 연결합니다.")
print("=" * 70)