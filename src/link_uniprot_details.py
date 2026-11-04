import pandas as pd
import requests
import time


INPUT_FILE = "data/processed/uniprot_targets.csv"
OUTPUT_FILE = "data/processed/uniprot_details.csv"


df = pd.read_csv(INPUT_FILE)


# 실제 UniProt ID만 추출
uniprot_ids = (
    df["UniProt_ID"]
    .dropna()
    .astype(str)
    .str.strip()
    .drop_duplicates()
    .tolist()
)


print("고유 UniProt ID:", len(uniprot_ids))
print()


session = requests.Session()

all_rows = []


for number, accession in enumerate(
    uniprot_ids,
    start=1
):

    print(
        f"[{number}/{len(uniprot_ids)}] "
        f"{accession}"
    )

    try:

        response = session.get(
            f"https://rest.uniprot.org/uniprotkb/{accession}.json",
            timeout=30
        )

        response.raise_for_status()

        data = response.json()


        # 단백질 이름
        protein_description = data.get(
            "proteinDescription",
            {}
        )

        recommended_name = (
            protein_description
            .get("recommendedName", {})
            .get("fullName", {})
            .get("value")
        )


        # 유전자 이름
        genes = data.get(
            "genes",
            []
        )

        gene_name = None

        if genes:

            gene_name = (
                genes[0]
                .get("geneName", {})
                .get("value")
            )


        # 생물종
        organism = data.get(
            "organism",
            {}
        )

        organism_name = organism.get(
            "scientificName"
        )


        # Swiss-Prot / TrEMBL
        reviewed = (
            data.get("entryType")
            == "UniProtKB reviewed (Swiss-Prot)"
        )


        all_rows.append({

            "UniProt_ID":
                accession,

            "Protein_Name":
                recommended_name,

            "Gene_Name":
                gene_name,

            "Organism":
                organism_name,

            "Reviewed":
                reviewed,

            "Entry_Type":
                data.get("entryType")
        })


    except Exception as e:

        print(
            "  -> 오류:",
            e
        )

        all_rows.append({

            "UniProt_ID":
                accession,

            "Protein_Name":
                None,

            "Gene_Name":
                None,

            "Organism":
                None,

            "Reviewed":
                None,

            "Entry_Type":
                None
        })


    time.sleep(0.2)


details = pd.DataFrame(
    all_rows
)


print()
print("================================")
print("UniProt 정보 수집 완료")
print("================================")

print(
    "전체 UniProt:",
    len(details)
)

print(
    "단백질명 확보:",
    details["Protein_Name"].notna().sum()
)

print(
    "유전자명 확보:",
    details["Gene_Name"].notna().sum()
)

print(
    "생물종 확보:",
    details["Organism"].notna().sum()
)

print(
    "Reviewed:",
    details["Reviewed"].eq(True).sum()
)

print()


details.to_csv(
    OUTPUT_FILE,
    index=False,
    encoding="utf-8-sig"
)


print(
    "저장 파일:",
    OUTPUT_FILE
)