import pandas as pd
import requests
import time


INPUT_FILE = "data/processed/plant_compounds_chembl.csv"
OUTPUT_FILE = "data/processed/chembl_activity.csv"


df = pd.read_csv(INPUT_FILE)

targets = df[
    df["ChEMBL_Status"] == "OK"
].copy()

print("전체 식물-화합물:", len(df))
print("ChEMBL 연결 성공:", len(targets))
print()


session = requests.Session()

all_rows = []


for number, (_, row) in enumerate(
    targets.iterrows(),
    start=1
):

    chembl_id = str(
        row["ChEMBL_ID"]
    ).strip()

    print(
        f"[{number}/{len(targets)}] "
        f"{chembl_id} | "
        f"{row['Compound_Name']}"
    )

    offset = 0
    total_for_compound = 0

    try:

        while True:

            response = session.get(
                "https://www.ebi.ac.uk/chembl/api/data/activity.json",
                params={
                    "molecule_chembl_id": chembl_id,
                    "limit": 1000,
                    "offset": offset
                },
                timeout=30
            )

            response.raise_for_status()

            data = response.json()

            activities = data.get(
                "activities",
                []
            )

            if not activities:
                break

            for activity in activities:

                all_rows.append({

                    "Plant_ID":
                        row["Plant_ID"],

                    "KNApSAcK_ID":
                        row["KNApSAcK_ID"],

                    "Compound_Name":
                        row["Compound_Name"],

                    "Chemical_InChIKey":
                        row["InChIKey"],

                    "ChEMBL_ID":
                        chembl_id,

                    "Activity_ID":
                        activity.get("activity_id"),

                    "Assay_ID":
                        activity.get("assay_id"),

                    "Target_ID":
                        activity.get("target_id"),

                    "Target_ChEMBL_ID":
                        activity.get("target_chembl_id"),

                    "Target_Name":
                        activity.get("target_pref_name"),

                    "Standard_Type":
                        activity.get("standard_type"),

                    "Standard_Value":
                        activity.get("standard_value"),

                    "Standard_Units":
                        activity.get("standard_units"),

                    "Standard_Relation":
                        activity.get("standard_relation"),

                    "pChEMBL":
                        activity.get("pchembl_value"),

                    "Activity_Comment":
                        activity.get("activity_comment"),

                    "Data_Validity_Comment":
                        activity.get(
                            "data_validity_comment"
                        ),

                    "Document_ChEMBL_ID":
                        activity.get(
                            "document_chembl_id"
                        )
                })

            total_for_compound += len(activities)

            print(
                f"  -> offset {offset}: "
                f"{len(activities)}개"
            )

            if len(activities) < 1000:
                break

            offset += 1000

            time.sleep(0.2)

        print(
            f"  -> 전체 Activity: "
            f"{total_for_compound}"
        )

    except Exception as e:

        print(
            "  -> 오류:",
            e
        )

    time.sleep(0.3)


activity_df = pd.DataFrame(
    all_rows
)


print()
print("================================")
print("ChEMBL Activity 수집 완료")
print("================================")

print(
    "Activity 전체:",
    len(activity_df)
)

if len(activity_df) > 0:

    print(
        "pChEMBL 존재:",
        activity_df["pChEMBL"].notna().sum()
    )

    print()
    print("ChEMBL 화합물 수:")
    print(
        activity_df["ChEMBL_ID"].nunique()
    )

    print()
    print("Standard_Type:")
    print(
        activity_df[
            "Standard_Type"
        ]
        .value_counts()
        .to_string()
    )


activity_df.to_csv(
    OUTPUT_FILE,
    index=False,
    encoding="utf-8-sig"
)


print()
print(
    "저장 파일:",
    OUTPUT_FILE
)