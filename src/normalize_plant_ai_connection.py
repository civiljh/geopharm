import pandas as pd


INPUT_FILE = "data/processed/plant_ai_connection.csv"
OUTPUT_FILE = "data/processed/plant_ai_connection_normalized.csv"


# ==================================================
# 1. 데이터 불러오기
# ==================================================

df = pd.read_csv(INPUT_FILE)

print("========================================")
print("기존 식물-AI 연결 데이터")
print("========================================")
print("행:", len(df))
print("식물 ID:", df["Plant_ID"].nunique())


# ==================================================
# 2. 표준 식물 학명 정의
# ==================================================

standard_names = {
    "PLANT001": "Panax ginseng",
    "PLANT002": "Angelica gigas",
    "PLANT003": "Astragalus mongholicus",
    "PLANT004": "Glycyrrhiza uralensis",
    "PLANT005": "Paeonia lactiflora",
    "PLANT006": "Conioselinum officinale",
    "PLANT007": "Schisandra chinensis",
    "PLANT008": "Lycium chinense",
    "PLANT009": "Rehmannia glutinosa",
    "PLANT010": "Ziziphus jujuba",
}


# ==================================================
# 3. Plant_ID를 기준으로 표준 학명 적용
# ==================================================

df["Standard_Scientific_Name"] = (
    df["Plant_ID"].map(standard_names)
)


# ==================================================
# 4. 표준 학명 연결 확인
# ==================================================

missing = df["Standard_Scientific_Name"].isna()

print()
print("========================================")
print("표준 학명 연결")
print("========================================")
print("전체 행:", len(df))
print("연결 성공:", (~missing).sum())
print("연결 실패:", missing.sum())


# ==================================================
# 5. 표준화 전/후 학명 비교
# ==================================================

print()
print("========================================")
print("기존 학명 → 표준 학명")
print("========================================")

name_comparison = (
    df[
        [
            "Plant_ID",
            "Scientific_Name",
            "Standard_Scientific_Name"
        ]
    ]
    .drop_duplicates()
    .sort_values(
        [
            "Plant_ID",
            "Scientific_Name"
        ]
    )
)

print(
    name_comparison.to_string(index=False)
)


# ==================================================
# 6. 표준 학명을 기존 컬럼에 적용
# ==================================================

df["Scientific_Name"] = (
    df["Standard_Scientific_Name"]
)

df = df.drop(
    columns=["Standard_Scientific_Name"]
)


# ==================================================
# 7. 중복 식물-화합물-단백질 관계 제거
# ==================================================

before = len(df)

df = df.drop_duplicates(
    subset=[
        "Plant_ID",
        "ChEMBL_ID",
        "UniProt_ID",
        "Standard_Type",
        "pChEMBL"
    ]
).copy()

after = len(df)

print()
print("========================================")
print("중복 제거")
print("========================================")
print("제거 전:", before)
print("제거 후:", after)
print("제거된 행:", before - after)


# ==================================================
# 8. 최종 식물별 화합물 수
# ==================================================

plant_summary = (
    df
    .groupby(
        [
            "Plant_ID",
            "Scientific_Name"
        ]
    )
    .agg(
        Connected_Compounds=(
            "ChEMBL_ID",
            "nunique"
        ),
        Connected_Proteins=(
            "UniProt_ID",
            "nunique"
        )
    )
    .reset_index()
)

print()
print("========================================")
print("표준화된 식물별 연결 현황")
print("========================================")

print(
    plant_summary.to_string(index=False)
)


# ==================================================
# 9. 저장
# ==================================================

df.to_csv(
    OUTPUT_FILE,
    index=False,
    encoding="utf-8-sig"
)

print()
print("========================================")
print("식물 학명 정규화 완료")
print("========================================")
print("최종 행:", len(df))
print("식물:", df["Plant_ID"].nunique())
print("화합물:", df["ChEMBL_ID"].nunique())
print("단백질:", df["UniProt_ID"].nunique())
print("저장:", OUTPUT_FILE)