import pandas as pd
import os


# ============================================================
# GeoPharm
# External Plant → Database
#
# 역할:
# 1. 사용자가 식물 정보를 입력
# 2. 기존 DB에 같은 학명이 있는지 확인
# 3. 없으면 다음 PLANT_ID를 자동 생성
# 4. 식물 기본정보를 DB에 저장
#
# 주의:
# 이 단계에서는 AI 분석을 아직 실행하지 않습니다.
# 다음 단계에서 화합물 → PubChem → ChEMBL → AI로 연결합니다.
# ============================================================


PLANT_FILE = "data/raw/medicinal_plants.csv"


# ------------------------------------------------------------
# 입력
# ------------------------------------------------------------

print()
print("=" * 60)
print("GeoPharm - External Plant Database")
print("=" * 60)

print()
print("새로운 약용식물 정보를 입력하세요.")
print("예: 어성초 / Houttuynia / Houttuynia cordata")
print()

common_name_ko = input("한국어 이름: ").strip()
english_name = input("영어 이름: ").strip()
scientific_name = input("학명: ").strip()


# ------------------------------------------------------------
# 기본 입력 검사
# ------------------------------------------------------------

if not scientific_name:

    print()
    print("학명이 입력되지 않았습니다.")
    print("프로그램을 종료합니다.")
    raise SystemExit


# ------------------------------------------------------------
# 기존 DB 확인
# ------------------------------------------------------------

if not os.path.exists(PLANT_FILE):

    print()
    print("ERROR: 식물 DB 파일을 찾을 수 없습니다.")
    print(PLANT_FILE)
    raise SystemExit


plants = pd.read_csv(
    PLANT_FILE,
    encoding="utf-8-sig"
)


# ------------------------------------------------------------
# 학명 중복 확인
# ------------------------------------------------------------

same_plant = plants[
    plants["Scientific_Name"]
    .astype(str)
    .str.strip()
    .str.lower()
    == scientific_name.lower()
]


if len(same_plant) > 0:

    print()
    print("=" * 60)
    print("이미 DB에 등록된 식물입니다.")
    print("=" * 60)

    print(
        same_plant.to_string(index=False)
    )

    print()
    print("새로운 식물로 추가하지 않습니다.")
    raise SystemExit


# ------------------------------------------------------------
# 다음 Plant_ID 자동 생성
# ------------------------------------------------------------

numbers = (
    plants["Plant_ID"]
    .astype(str)
    .str.extract(
        r"PLANT(\d+)",
        expand=False
    )
)

numbers = pd.to_numeric(
    numbers,
    errors="coerce"
)

next_number = int(numbers.max()) + 1

new_plant_id = f"PLANT{next_number:03d}"


# ------------------------------------------------------------
# 새로운 식물 생성
# ------------------------------------------------------------

new_plant = pd.DataFrame([
    {
        "Plant_ID": new_plant_id,
        "Common_Name_KO": common_name_ko,
        "English_Name": english_name,
        "Scientific_Name": scientific_name
    }
])


# ------------------------------------------------------------
# DB에 추가
# ------------------------------------------------------------

plants = pd.concat(
    [
        plants,
        new_plant
    ],
    ignore_index=True
)


# ------------------------------------------------------------
# 저장
# ------------------------------------------------------------

plants.to_csv(
    PLANT_FILE,
    index=False,
    encoding="utf-8-sig"
)


# ------------------------------------------------------------
# 결과
# ------------------------------------------------------------

print()
print("=" * 60)
print("새로운 식물이 DB에 추가되었습니다.")
print("=" * 60)

print()
print("Plant_ID       :", new_plant_id)
print("한국어 이름    :", common_name_ko)
print("영어 이름      :", english_name)
print("학명           :", scientific_name)

print()
print("저장 위치:")
print(PLANT_FILE)

print()
print("현재 식물 DB 개수:", len(plants))

print()
print("다음 단계:")
print("외부 화합물 검색 → PubChem → ChEMBL → AI 분석")