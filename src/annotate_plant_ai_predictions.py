import time
import requests
import pandas as pd

INPUT_FILE = "data/processed/plant_ai_predictions.csv"
OUTPUT_FILE = "data/processed/plant_ai_annotated.csv"

print("=== GeoPharm AI Prediction UniProt Annotation ===")

# --------------------------------------------------
# 1. AI prediction 데이터 읽기
# --------------------------------------------------

df = pd.read_csv(INPUT_FILE)

print(f"예측 데이터 행 수: {len(df):,}")
print(f"UniProt ID 종류: {df['UniProt_ID'].nunique():,}")

# --------------------------------------------------
# 2. UniProt ID 목록 만들기
# --------------------------------------------------

uniprot_ids = (
    df["UniProt_ID"]
    .dropna()
    .astype(str)
    .str.strip()
    .unique()
    .tolist()
)

print(f"조회할 UniProt ID: {len(uniprot_ids):,}")

# --------------------------------------------------
# 3. UniProt API 조회
# --------------------------------------------------

session = requests.Session()

annotation_rows = []

success_count = 0
failed_count = 0

for i, uniprot_id in enumerate(uniprot_ids, start=1):

    url = f"https://rest.uniprot.org/uniprotkb/{uniprot_id}.json"

    try:
        response = session.get(url, timeout=30)

        if response.status_code != 200:
            print(
                f"[{i}/{len(uniprot_ids)}] "
                f"{uniprot_id} -> HTTP {response.status_code}"
            )
            failed_count += 1
            continue

        data = response.json()

        # --------------------------------------------------
        # Protein name
        # --------------------------------------------------

        protein_name = (
            data
            .get("proteinDescription", {})
            .get("recommendedName", {})
            .get("fullName", {})
            .get("value")
        )

        # --------------------------------------------------
        # Gene name
        # --------------------------------------------------

        genes = data.get("genes", [])

        gene_name = None

        if genes:
            gene_name = (
                genes[0]
                .get("geneName", {})
                .get("value")
            )

        # --------------------------------------------------
        # Organism
        # --------------------------------------------------

        organism = (
            data
            .get("organism", {})
            .get("scientificName")
        )

        # --------------------------------------------------
        # Entry name
        # --------------------------------------------------

        entry_name = data.get("uniProtkbId")

        # --------------------------------------------------
        # Reviewed / Swiss-Prot 여부
        # --------------------------------------------------

        entry_type = data.get("entryType")

        reviewed = (
            entry_type == "UniProtKB reviewed (Swiss-Prot)"
        )

        annotation_rows.append({
            "UniProt_ID": uniprot_id,
            "Protein_Name": protein_name,
            "Gene_Name": gene_name,
            "Organism": organism,
            "UniProt_Entry_Name": entry_name,
            "UniProt_Reviewed": reviewed,
        })

        success_count += 1

        if i % 25 == 0 or i == len(uniprot_ids):
            print(
                f"[{i}/{len(uniprot_ids)}] "
                f"성공 {success_count}, 실패 {failed_count}"
            )

        time.sleep(0.1)

    except Exception as e:

        print(
            f"[{i}/{len(uniprot_ids)}] "
            f"{uniprot_id} -> ERROR: {e}"
        )

        failed_count += 1

# --------------------------------------------------
# 4. Annotation 데이터 생성
# --------------------------------------------------

annotation_df = pd.DataFrame(annotation_rows)

print()
print("=== UniProt 조회 결과 ===")
print(f"성공: {success_count:,}")
print(f"실패: {failed_count:,}")
print(f"Annotation 행 수: {len(annotation_df):,}")

# --------------------------------------------------
# 5. AI prediction과 병합
# --------------------------------------------------

result = df.merge(
    annotation_df,
    on="UniProt_ID",
    how="left"
)

# --------------------------------------------------
# 6. 저장
# --------------------------------------------------

result.to_csv(
    OUTPUT_FILE,
    index=False,
    encoding="utf-8-sig"
)

print()
print("=== 완료 ===")
print(f"최종 행 수: {len(result):,}")
print(f"최종 열 수: {len(result.columns):,}")
print(f"저장 파일: {OUTPUT_FILE}")

print()
print("추가된 열:")
print("Protein_Name")
print("Gene_Name")
print("Organism")
print("UniProt_Entry_Name")
print("UniProt_Reviewed")