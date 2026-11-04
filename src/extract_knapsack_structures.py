import pandas as pd
import requests
import re
import time
from bs4 import BeautifulSoup


INPUT_FILE = "data/raw/plant_compounds_pubchem_final.csv"
OUTPUT_FILE = "data/raw/plant_compounds_structures.csv"


df = pd.read_csv(INPUT_FILE)

# PubChem 연결에 실패한 물질만 처리
fail_mask = df["PubChem_Status"] == "FAIL"
target = df[fail_mask].copy()

print("전체 데이터:", len(df))
print("PubChem 미연결:", len(target))
print()


session = requests.Session()

results = []


for number, (index, row) in enumerate(
    target.iterrows(),
    start=1
):

    plant_id = str(row["Plant_ID"])
    knapsack_id = str(row["KNApSAcK_ID"])
    compound_name = str(row["Compound_Name"])

    print(
        f"[{number}/{len(target)}] "
        f"{plant_id} | "
        f"{knapsack_id} | "
        f"{compound_name}"
    )

    smiles = None
    inchicode = None
    status = "FAIL"

    try:

        url = (
            "https://www.knapsackfamily.com/"
            "knapsack_core/information.php?word="
            + requests.utils.quote(
                knapsack_id,
                safe=""
            )
        )

        response = session.get(
            url,
            timeout=20
        )

        if response.status_code == 200:

            soup = BeautifulSoup(
                response.text,
                "html.parser"
            )

            text = soup.get_text(
                " ",
                strip=True
            )

            # InChI 추출
            inchicode_match = re.search(
                r"InChICode\s+"
                r"(InChI=1S/[^\s]+)",
                text,
                re.I
            )

            if inchicode_match:

                inchicode = (
                    inchicode_match.group(1)
                )

            # SMILES 추출
            smiles_match = re.search(
                r"SMILES\s+"
                r"(.+?)"
                r"\s+Start Substs",
                text,
                re.I
            )

            if smiles_match:

                smiles = (
                    smiles_match.group(1)
                    .strip()
                )

                status = "OK"

                print(
                    "  -> SMILES 추출 성공"
                )

            else:

                print(
                    "  -> SMILES를 찾지 못함"
                )

        else:

            print(
                f"  -> HTTP {response.status_code}"
            )

    except Exception as e:

        print(
            f"  -> 오류: {e}"
        )

    results.append(
        {
            "Plant_ID": plant_id,
            "KNApSAcK_ID": knapsack_id,
            "KNApSAcK_SMILES": smiles,
            "KNApSAcK_InChI": inchicode,
            "KNApSAcK_Structure_Status": status,
        }
    )

    time.sleep(0.3)


# 구조식 결과를 DataFrame으로 변환
structure_df = pd.DataFrame(results)


# Plant_ID + KNApSAcK_ID를 함께 사용하여 결합
final_df = df.merge(
    structure_df,
    on=[
        "Plant_ID",
        "KNApSAcK_ID"
    ],
    how="left"
)


# 저장
final_df.to_csv(
    OUTPUT_FILE,
    index=False,
    encoding="utf-8-sig"
)


print()
print("================================")
print("KNApSAcK 구조식 추출 완료")
print("================================")

print(
    "전체 데이터:",
    len(final_df)
)

print(
    "SMILES 추출 성공:",
    (
        final_df["KNApSAcK_Structure_Status"]
        == "OK"
    ).sum()
)

print(
    "SMILES 추출 실패:",
    (
        (final_df["PubChem_Status"] == "FAIL")
        &
        (
            final_df[
                "KNApSAcK_Structure_Status"
            ] != "OK"
        )
    ).sum()
)

print()
print(
    "저장 파일:",
    OUTPUT_FILE
)