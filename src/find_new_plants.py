import pandas as pd
import os


# ============================================================
# GeoPharm
# 새 식물 자동 감지 프로그램
# ============================================================
#
# 역할:
# 1. 식물 DB 확인
# 2. AI 예측 완료 식물 확인
# 3. 아직 AI 분석이 완료되지 않은 식물 찾기
#
# 기존 데이터 파일은 수정하지 않습니다.
# ============================================================


PLANT_FILE = "data/raw/medicinal_plants.csv"
AI_FILE = "data/processed/plant_ai_predictions.csv"

OUTPUT_FILE = "data/processed/new_plants_to_process.csv"


# ------------------------------------------------------------
# 파일 확인
# ------------------------------------------------------------

if not os.path.exists(PLANT_FILE):
    print()
    print("ERROR: 식물 DB 파일을 찾을 수 없습니다.")
    print(PLANT_FILE)
    raise SystemExit

if not os.path.exists(AI_FILE):
    print()
    print("ERROR: AI 예측 파일을 찾을 수 없습니다.")
    print(AI_FILE)
    raise SystemExit


# ------------------------------------------------------------
# 데이터 읽기
# ------------------------------------------------------------

plants = pd.read_csv(
    PLANT_FILE,
    encoding="utf-8-sig"
)

ai_predictions = pd.read_csv(
    AI_FILE,
    encoding="utf-8-sig"
)


# ------------------------------------------------------------
# Plant_ID 정리
# ------------------------------------------------------------

plants["Plant_ID"] = (
    plants["Plant_ID"]
    .astype(str)
    .str.strip()
)

ai_predictions["Plant_ID"] = (
    ai_predictions["Plant_ID"]
    .astype(str)
    .str.strip()
)


# ------------------------------------------------------------
# AI 분석 완료 식물 목록
# ------------------------------------------------------------

processed_ids = set(
    ai_predictions["Plant_ID"].dropna().unique()
)


# ------------------------------------------------------------
# 아직 AI 분석이 완료되지 않은 식물 찾기
# ------------------------------------------------------------

new_plants = plants[
    ~plants["Plant_ID"].isin(processed_ids)
].copy()


# ------------------------------------------------------------
# 결과 출력
# ------------------------------------------------------------

print()
print("=" * 70)
print("GeoPharm 새 식물 자동 감지")
print("=" * 70)

print()
print("식물 DB 전체:", len(plants))
print("AI 분석 완료:", len(processed_ids))
print("아직 AI 분석되지 않은 식물:", len(new_plants))


print()

if len(new_plants) == 0:

    print("=" * 70)
    print("새로 처리할 식물이 없습니다.")
    print("=" * 70)

else:

    print("=" * 70)
    print("처리 대상 식물")
    print("=" * 70)

    print()

    print(
        new_plants[
            [
                "Plant_ID",
                "Common_Name_KO",
                "English_Name",
                "Scientific_Name"
            ]
        ].to_string(index=False)
    )


# ------------------------------------------------------------
# 저장
# ------------------------------------------------------------

new_plants.to_csv(
    OUTPUT_FILE,
    index=False,
    encoding="utf-8-sig"
)


print()
print("=" * 70)
print("새 식물 목록 저장 완료")
print("=" * 70)

print()
print("저장 파일:")
print(OUTPUT_FILE)

print()
print("완료.")