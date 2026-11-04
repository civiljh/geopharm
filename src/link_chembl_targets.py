import pandas as pd
import requests
import time


INPUT_FILE = "data/processed/chembl_affinity.csv"
OUTPUT_FILE = "data/processed/chembl_targets.csv"


df = pd.read_csv(INPUT_FILE)


# ChEMBL Target ID가 존재하는 데이터만 사용
targets = df[
    df["Target_ChEMBL_ID"].notna()
].copy()


target_ids = (
    targets["Target_ChEMBL_ID"]
    .astype(str)
    .str.strip()
    .unique()
)


print("Affinity 데이터:", len(df))
print("고유 Target_ChEMBL_ID:", len(target_ids))
print()


session = requests.Session()

all_rows = []


for number, target_id in enumerate(
    target_ids,
    start=1
):

    print(
        f"[{number}/{len(target_ids)}] "
        f"{target_id}"
    )

    try:

        response = session.get(
            f"https://www.ebi.ac.uk/chembl/api/data/target/{target_id}.json",
            timeout=30
        )

        response.raise_for_status()

        target = response.json()

        all_rows.append({

            "Target_ChEMBL_ID":
                target_id,

            "Target_Type":
                target.get("target_type"),

            "Target_Name":
                target.get("pref_name"),

            "Target_Organism":
                target.get("organism"),

            "Target_Organism_ID":
                target.get("tax_id"),

            "Target_Chembl_Name":
                target.get("chembl_name")
        })

    except Exception as e:

        print(
            "  -> 오류:",
            e
        )

        all_rows.append({

            "Target_ChEMBL_ID":
                target_id,

            "Target_Type":
                None,

            "Target_Name":
                None,

            "Target_Organism":
                None,

            "Target_Organism_ID":
                None,

            "Target_Chembl_Name":
                None
        })

    time.sleep(0.2)


target_df = pd.DataFrame(
    all_rows
)


print()
print("================================")
print("ChEMBL Target 수집 완료")
print("================================")

print(
    "Target 전체:",
    len(target_df)
)

print()


print("Target_Type:")
print(
    target_df[
        "Target_Type"
    ]
    .value_counts(dropna=False)
    .to_string()
)

print()


print("Organism:")
print(
    target_df[
        "Target_Organism"
    ]
    .value_counts()
    .head(20)
    .to_string()
)


target_df.to_csv(
    OUTPUT_FILE,
    index=False,
    encoding="utf-8-sig"
)


print()
print(
    "저장 파일:",
    OUTPUT_FILE
)