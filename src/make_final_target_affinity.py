import pandas as pd

AFFINITY_FILE = "data/processed/target_affinity.csv"
UNIPROT_FILE = "data/processed/uniprot_targets.csv"
OUTPUT_FILE = "data/processed/final_target_affinity.csv"

print("파일 읽는 중...")

affinity = pd.read_csv(AFFINITY_FILE)
uniprot = pd.read_csv(UNIPROT_FILE)

print("Target Affinity:", len(affinity))
print("UniProt:", len(uniprot))
print()

# UniProt 정보에서 필요한 열만 사용
uniprot_columns = [
    "UniProt_ID",
    "Protein_Name",
    "Gene_Name",
    "Organism",
    "Entry_Type",
    "UniProt_Status"
]

uniprot = uniprot[uniprot_columns]

# UniProt ID를 기준으로 단백질 정보 연결
final_df = affinity.merge(
    uniprot,
    on="UniProt_ID",
    how="left"
)

print("================================")
print("최종 Target-Affinity 데이터 생성")
print("================================")

print("전체 레코드:", len(final_df))

print(
    "Protein_Name 확보:",
    final_df["Protein_Name"].notna().sum()
)

print(
    "Gene_Name 확보:",
    final_df["Gene_Name"].notna().sum()
)

print(
    "Organism 확보:",
    final_df["Organism"].notna().sum()
)

print(
    "UniProt reviewed:",
    (
        final_df["Entry_Type"]
        == "UniProtKB reviewed (Swiss-Prot)"
    ).sum()
)

print()

final_df.to_csv(
    OUTPUT_FILE,
    index=False,
    encoding="utf-8-sig"
)

print("저장 파일:", OUTPUT_FILE)