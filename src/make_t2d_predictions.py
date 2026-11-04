import pandas as pd
from pathlib import Path


# ============================================================
# GeoPharm - 자동 T2D 예측 추출
#
# 역할:
# 1. GeoPharm 전체 식물 AI 예측 데이터를 읽는다.
# 2. T2D 표적 목록과 비교한다.
# 3. T2D 관련 표적만 자동으로 추출한다.
# 4. 특정 식물 ID를 코드에 직접 지정하지 않는다.
#
# 따라서 PLANT031, PLANT032, PLANT033...이 추가되어도
# AI 예측 파일에 들어오기만 하면 자동으로 분석된다.
# ============================================================


PREDICTION_FILE = Path(
    "data/processed/plant_ai_predictions.csv"
)

TARGET_FILE = Path(
    "data/processed/t2d_target_list.csv"
)

OUTPUT_FILE = Path(
    "data/processed/t2d_plant_predictions.csv"
)


print("=" * 70)
print("GeoPharm - 자동 T2D AI 예측 분석")
print("=" * 70)


# ============================================================
# 1. AI 예측 데이터 읽기
# ============================================================

print()
print("[1] AI 예측 데이터 불러오기")

pred = pd.read_csv(
    PREDICTION_FILE,
    low_memory=False
)

print(f"AI 예측 행: {len(pred):,}")
print(f"AI 식물 수: {pred['Plant_ID'].nunique()}")


# ============================================================
# 2. T2D 표적 목록 읽기
# ============================================================

print()
print("[2] T2D 표적 목록 불러오기")

targets = pd.read_csv(TARGET_FILE)

target_ids = (
    targets["UniProt_ID"]
    .dropna()
    .astype(str)
    .unique()
)

target_ids = set(target_ids)

print(f"T2D 표적 수: {len(target_ids)}")

print()
print("T2D UniProt ID:")
for target_id in sorted(target_ids):
    print(f"  {target_id}")


# ============================================================
# 3. UniProt ID 정리
# ============================================================

pred["UniProt_ID"] = (
    pred["UniProt_ID"]
    .astype(str)
    .str.strip()
)

targets["UniProt_ID"] = (
    targets["UniProt_ID"]
    .astype(str)
    .str.strip()
)


# ============================================================
# 4. T2D 관련 AI 예측만 추출
# ============================================================

print()
print("[3] T2D 관련 AI 예측 추출")

t2d = pred[
    pred["UniProt_ID"].isin(target_ids)
].copy()

print(f"T2D 관련 예측 행: {len(t2d):,}")
print(f"T2D 관련 식물 수: {t2d['Plant_ID'].nunique()}")
print(f"T2D 관련 화합물 수: {t2d['ChEMBL_ID'].nunique()}")
print(f"T2D 관련 표적 수: {t2d['UniProt_ID'].nunique()}")


# ============================================================
# 5. 표적 정보 연결
# ============================================================

print()
print("[4] T2D 표적 상세 정보 연결")

target_columns = [
    "UniProt_ID",
    "Gene_Name",
    "Protein_Name",
    "Disease",
    "Target_Evidence",
    "Target_Role",
    "Evidence_Note",
]

target_info = targets[target_columns].drop_duplicates(
    subset=["UniProt_ID"]
)


t2d = t2d.merge(
    target_info,
    on="UniProt_ID",
    how="left"
)


# ============================================================
# 6. 필요한 열 선택
# ============================================================

columns = [
    "Plant_ID",
    "Scientific_Name",
    "Common_Name_KO",
    "Compound_Name",
    "ChEMBL_ID",
    "UniProt_ID",
    "Protein_Name",
    "Gene_Name",
    "Disease",
    "Predicted_pChEMBL",
    "Target_Evidence",
    "Target_Role",
    "Evidence_Note",
]

# 실제 파일에 존재하는 열만 사용
columns = [
    c for c in columns
    if c in t2d.columns
]

t2d = t2d[columns]


# ============================================================
# 7. 중복 제거
# ============================================================

before = len(t2d)

t2d = t2d.drop_duplicates()

after = len(t2d)

print()
print(f"중복 제거 전: {before:,}")
print(f"중복 제거 후: {after:,}")
print(f"제거된 중복: {before - after:,}")


# ============================================================
# 8. AI 예측 점수가 높은 순서로 정렬
# ============================================================

t2d = t2d.sort_values(
    "Predicted_pChEMBL",
    ascending=False
)


# ============================================================
# 9. 저장
# ============================================================

OUTPUT_FILE.parent.mkdir(
    parents=True,
    exist_ok=True
)

t2d.to_csv(
    OUTPUT_FILE,
    index=False,
    encoding="utf-8-sig"
)


# ============================================================
# 10. 전체 결과
# ============================================================

print()
print("=" * 70)
print("T2D 자동 분석 완료")
print("=" * 70)

print(f"저장 파일: {OUTPUT_FILE}")
print(f"전체 T2D 예측 행: {len(t2d):,}")
print(f"식물 수: {t2d['Plant_ID'].nunique()}")
print(f"화합물 수: {t2d['ChEMBL_ID'].nunique()}")
print(f"표적 수: {t2d['UniProt_ID'].nunique()}")


# ============================================================
# 11. 식물별 결과
# ============================================================

print()
print("=" * 70)
print("식물별 T2D 예측 수")
print("=" * 70)

plant_counts = (
    t2d.groupby("Plant_ID")
    .size()
    .sort_values(ascending=False)
)

print(plant_counts.to_string())


# ============================================================
# 12. 표적별 결과
# ============================================================

print()
print("=" * 70)
print("T2D 표적별 결과")
print("=" * 70)

target_counts = (
    t2d.groupby(
        ["Gene_Name", "Protein_Name"]
    )["ChEMBL_ID"]
    .nunique()
    .sort_values(ascending=False)
)

print(target_counts.to_string())


# ============================================================
# 13. 상위 후보 20개
# ============================================================

print()
print("=" * 70)
print("T2D AI 상위 후보 20개")
print("=" * 70)

top_columns = [
    "Plant_ID",
    "Scientific_Name",
    "Compound_Name",
    "ChEMBL_ID",
    "Gene_Name",
    "Predicted_pChEMBL",
]

top_columns = [
    c for c in top_columns
    if c in t2d.columns
]

print(
    t2d[top_columns]
    .head(20)
    .to_string(index=False)
)


# ============================================================
# 14. 새 식물 자동 포함 확인
# ============================================================

if "PLANT031" in t2d["Plant_ID"].astype(str).unique():

    plant031 = t2d[
        t2d["Plant_ID"].astype(str) == "PLANT031"
    ]

    print()
    print("=" * 70)
    print("PLANT031 자동 포함 확인")
    print("=" * 70)

    print(
        f"PLANT031 T2D 예측 행: {len(plant031):,}"
    )

    print(
        f"PLANT031 T2D 표적 수: "
        f"{plant031['UniProt_ID'].nunique()}"
    )

else:

    print()
    print("PLANT031은 T2D 예측 결과에 없습니다.")


print()
print("=" * 70)
print("완료")
print("=" * 70)