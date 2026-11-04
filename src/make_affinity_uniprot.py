import pandas as pd


AFFINITY_FILE = "data/processed/chembl_affinity.csv"
TARGET_FILE = "data/processed/uniprot_targets.csv"
DETAIL_FILE = "data/processed/uniprot_details.csv"

OUTPUT_FILE = "data/processed/affinity_uniprot.csv"


print("데이터 불러오는 중...")


affinity = pd.read_csv(
    AFFINITY_FILE
)

targets = pd.read_csv(
    TARGET_FILE
)

details = pd.read_csv(
    DETAIL_FILE
)


print("Affinity:", len(affinity))
print("Target-UniProt:", len(targets))
print("UniProt 상세:", len(details))
print()


# --------------------------------------------------
# 1. Affinity → ChEMBL Target → UniProt
# --------------------------------------------------

merged = affinity.merge(
    targets[
        [
            "Target_ChEMBL_ID",
            "Target_Type",
            "UniProt_ID"
        ]
    ],
    on="Target_ChEMBL_ID",
    how="left"
)


# --------------------------------------------------
# 2. UniProt → 단백질 상세정보
# --------------------------------------------------

merged = merged.merge(
    details[
        [
            "UniProt_ID",
            "Protein_Name",
            "Gene_Name",
            "Organism",
            "Reviewed",
            "Entry_Type"
        ]
    ],
    on="UniProt_ID",
    how="left"
)


# --------------------------------------------------
# 3. 결과 확인
# --------------------------------------------------

print("================================")
print("Affinity → UniProt 연결 완료")
print("================================")

print(
    "전체 Affinity:",
    len(merged)
)

print(
    "UniProt 연결:",
    merged["UniProt_ID"].notna().sum()
)

print(
    "UniProt 연결 실패:",
    merged["UniProt_ID"].isna().sum()
)

print(
    "단백질명 확보:",
    merged["Protein_Name"].notna().sum()
)

print(
    "유전자명 확보:",
    merged["Gene_Name"].notna().sum()
)

print(
    "사람 단백질:",
    (
        merged["Organism"]
        == "Homo sapiens"
    ).sum()
)

print()


print("Target_Type:")
print(
    merged["Target_Type"]
    .value_counts(dropna=False)
    .to_string()
)

print()


print("Standard_Type:")
print(
    merged["Standard_Type"]
    .value_counts()
    .to_string()
)

print()


print("고유 화합물:")
print(
    merged["ChEMBL_ID"].nunique()
)

print(
    "고유 UniProt:",
    merged["UniProt_ID"].nunique()
)

print(
    "고유 Target:",
    merged["Target_ChEMBL_ID"].nunique()
)


# --------------------------------------------------
# 4. 저장
# --------------------------------------------------

merged.to_csv(
    OUTPUT_FILE,
    index=False,
    encoding="utf-8-sig"
)


print()
print(
    "저장 파일:",
    OUTPUT_FILE
)