import pandas as pd
import requests
import time


INPUT_FILE = "data/raw/plant_compounds_pubchem.csv"
OUTPUT_FILE = "data/raw/plant_compounds_pubchem_final.csv"


df = pd.read_csv(INPUT_FILE)

# PubChem 검색 실패 데이터만 선택
fail_mask = df["PubChem_Status"] == "FAIL"

print("PubChem 기존 성공:", (~fail_mask).sum())
print("CAS 재검색 대상:", fail_mask.sum())
print()


session = requests.Session()

success_count = 0
fail_count = 0


for index in df[fail_mask].index:

    cas = str(df.loc[index, "CAS"]).strip()
    compound_name = str(df.loc[index, "Compound_Name"]).strip()

    print(
        f"[{success_count + fail_count + 1}/{fail_mask.sum()}] "
        f"{compound_name} | CAS: {cas}"
    )

    try:

        url = (
            "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/"
            + requests.utils.quote(cas, safe="")
            + "/property/Title,IsomericSMILES,InChIKey/JSON"
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

            df.loc[index, "PubChem_CID"] = properties.get("CID")
            df.loc[index, "PubChem_Title"] = properties.get("Title")
            df.loc[index, "PubChem_SMILES"] = properties.get("SMILES")
            df.loc[index, "InChIKey"] = properties.get("InChIKey")
            df.loc[index, "PubChem_Status"] = "OK_CAS"

            success_count += 1

            print(
                "  -> 연결 성공:",
                properties.get("Title")
            )

        else:

            print(
                "  -> PubChem 미등록"
            )

            fail_count += 1

    except Exception as e:

        print(
            "  -> 오류:",
            e
        )

        fail_count += 1

    time.sleep(0.2)


# 최종 파일 저장
df.to_csv(
    OUTPUT_FILE,
    index=False,
    encoding="utf-8-sig"
)


print()
print("================================")
print("CAS 재검색 완료")
print("================================")
print(
    "기존 PubChem 성공:",
    (~fail_mask).sum()
)
print(
    "CAS 검색 추가 성공:",
    success_count
)
print(
    "최종 PubChem 연결 성공:",
    (df["PubChem_Status"] != "FAIL").sum()
)
print(
    "최종 PubChem 미연결:",
    (df["PubChem_Status"] == "FAIL").sum()
)
print()
print(
    "저장 파일:",
    OUTPUT_FILE
)