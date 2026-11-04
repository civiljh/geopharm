import pandas as pd
import requests
import time

INPUT_FILE = "data/raw/plant_compounds.csv"
OUTPUT_FILE = "data/raw/plant_compounds_pubchem.csv"

PUBCHEM_URL = (
    "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/"
    "{}/property/Title,IsomericSMILES,InChIKey/JSON"
)

df = pd.read_csv(INPUT_FILE)

print("전체 KNApSAcK 성분:", len(df))
print()

results = []

session = requests.Session()

for i, row in df.iterrows():

    compound_name = str(row["Compound_Name"])

    print(
        f"[{i + 1}/{len(df)}] "
        f"{compound_name}"
    )

    cid = None
    title = None
    smiles = None
    inchikey = None
    status = "FAIL"

    try:
        url = PUBCHEM_URL.format(
            requests.utils.quote(
                compound_name,
                safe=""
            )
        )

        response = session.get(
            url,
            timeout=20
        )

        if response.status_code == 200:

            data = response.json()

            properties = (
                data["PropertyTable"]["Properties"][0]
            )

            cid = properties.get("CID")
            title = properties.get("Title")
            smiles = properties.get("SMILES")
            inchikey = properties.get("InChIKey")

            status = "OK"

        else:
            print(
                f"  PubChem 검색 실패: "
                f"HTTP {response.status_code}"
            )

    except Exception as e:

        print(
            f"  오류: {e}"
        )

    results.append(
        {
            "PubChem_CID": cid,
            "PubChem_Title": title,
            "PubChem_SMILES": smiles,
            "InChIKey": inchikey,
            "PubChem_Status": status,
        }
    )

    time.sleep(0.2)


pubchem_df = pd.DataFrame(results)

final_df = pd.concat(
    [
        df.reset_index(drop=True),
        pubchem_df
    ],
    axis=1
)

final_df.to_csv(
    OUTPUT_FILE,
    index=False,
    encoding="utf-8-sig"
)

print()
print("================================")
print("PubChem 연결 완료")
print("================================")
print("전체 성분:", len(final_df))
print(
    "PubChem 연결 성공:",
    (final_df["PubChem_Status"] == "OK").sum()
)
print(
    "PubChem 연결 실패:",
    (final_df["PubChem_Status"] == "FAIL").sum()
)
print()
print("저장 파일:", OUTPUT_FILE)