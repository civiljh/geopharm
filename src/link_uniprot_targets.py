import pandas as pd
import requests
import time


INPUT_FILE = "data/processed/chembl_targets.csv"
OUTPUT_FILE = "data/processed/uniprot_targets.csv"


targets = pd.read_csv(INPUT_FILE)

print("전체 ChEMBL Target:", len(targets))
print()

session = requests.Session()

all_rows = []


for number, (_, row) in enumerate(
    targets.iterrows(),
    start=1
):

    target_id = str(
        row["Target_ChEMBL_ID"]
    ).strip()

    print(
        f"[{number}/{len(targets)}] "
        f"{target_id}"
    )

    uniprot_ids = []

    try:

        response = session.get(
            f"https://www.ebi.ac.uk/chembl/api/data/target/{target_id}.json",
            timeout=30
        )

        response.raise_for_status()

        target = response.json()

        components = target.get(
            "target_components",
            []
        )

        for component in components:

            # accession만 실제 UniProt ID로 사용
            accession = component.get(
                "accession"
            )

            if accession:

                accession = str(
                    accession
                ).strip()

                if accession:
                    uniprot_ids.append(
                        accession
                    )

        # 중복 제거
        uniprot_ids = list(
            dict.fromkeys(
                uniprot_ids
            )
        )

        print(
            "  -> UniProt:",
            ", ".join(uniprot_ids)
            if uniprot_ids
            else "없음"
        )

    except Exception as e:

        print(
            "  -> 오류:",
            e
        )

    # UniProt ID가 여러 개일 수 있으므로
    # 하나씩 별도 행으로 저장
    if uniprot_ids:

        for accession in uniprot_ids:

            all_rows.append({

                "Target_ChEMBL_ID":
                    target_id,

                "Target_Type":
                    row["Target_Type"],

                "Target_Name":
                    row["Target_Name"],

                "Target_Organism":
                    row["Target_Organism"],

                "UniProt_ID":
                    accession
            })

    else:

        all_rows.append({

            "Target_ChEMBL_ID":
                target_id,

            "Target_Type":
                row["Target_Type"],

            "Target_Name":
                row["Target_Name"],

            "Target_Organism":
                row["Target_Organism"],

            "UniProt_ID":
                None
        })

    time.sleep(0.2)


uniprot_df = pd.DataFrame(
    all_rows
)


print()
print("================================")
print("ChEMBL → UniProt 연결 완료")
print("================================")

print(
    "Target 행:",
    len(uniprot_df)
)

print(
    "UniProt 연결 성공:",
    uniprot_df["UniProt_ID"].notna().sum()
)

print(
    "UniProt 연결 실패:",
    uniprot_df["UniProt_ID"].isna().sum()
)

print()


print("UniProt ID 종류:")
print(
    uniprot_df[
        "UniProt_ID"
    ]
    .dropna()
    .nunique()
)


uniprot_df.to_csv(
    OUTPUT_FILE,
    index=False,
    encoding="utf-8-sig"
)


print()
print(
    "저장 파일:",
    OUTPUT_FILE
)