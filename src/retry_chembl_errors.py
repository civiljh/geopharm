import pandas as pd
import requests
import time


INPUT_FILE = "data/processed/plant_compounds_chembl.csv"
OUTPUT_FILE = "data/processed/plant_compounds_chembl.csv"


df = pd.read_csv(INPUT_FILE)


# 오류가 발생한 행만 재시도
retry_mask = ~df["ChEMBL_Status"].isin(
    ["OK", "NOT_FOUND"]
)

target = df[retry_mask].copy()


print("전체 데이터:", len(df))
print("재시도 대상:", len(target))
print()


session = requests.Session()


for number, (index, row) in enumerate(
    target.iterrows(),
    start=1
):

    inchikey = str(
        row["Chemical_InChIKey"]
    ).strip()

    print(
        f"[{number}/{len(target)}] "
        f"{row['KNApSAcK_ID']} | "
        f"{row['Compound_Name']}"
    )

    try:

        url = (
            "https://www.ebi.ac.uk/chembl/api/data/"
            "molecule.json?"
            "molecule_structures__standard_inchi_key="
            + requests.utils.quote(
                inchikey,
                safe=""
            )
        )

        response = session.get(
            url,
            timeout=30
        )

        if response.status_code == 200:

            data = response.json()
            molecules = data.get(
                "molecules",
                []
            )

            if len(molecules) > 0:

                molecule = molecules[0]

                properties = (
                    molecule.get(
                        "molecule_properties"
                    )
                    or {}
                )

                structures = (
                    molecule.get(
                        "molecule_structures"
                    )
                    or {}
                )

                df.loc[
                    index,
                    "ChEMBL_ID"
                ] = molecule.get(
                    "molecule_chembl_id"
                )

                df.loc[
                    index,
                    "ChEMBL_Name"
                ] = molecule.get(
                    "pref_name"
                )

                df.loc[
                    index,
                    "ChEMBL_MolecularFormula"
                ] = properties.get(
                    "full_molformula"
                )

                df.loc[
                    index,
                    "ChEMBL_MolecularWeight"
                ] = properties.get(
                    "full_mwt"
                )

                df.loc[
                    index,
                    "ChEMBL_AlogP"
                ] = properties.get(
                    "alogp"
                )

                df.loc[
                    index,
                    "ChEMBL_HBA"
                ] = properties.get(
                    "hba"
                )

                df.loc[
                    index,
                    "ChEMBL_HBD"
                ] = properties.get(
                    "hbd"
                )

                df.loc[
                    index,
                    "ChEMBL_PSA"
                ] = properties.get(
                    "psa"
                )

                df.loc[
                    index,
                    "ChEMBL_QED"
                ] = properties.get(
                    "qed_weighted"
                )

                df.loc[
                    index,
                    "ChEMBL_CanonicalSMILES"
                ] = structures.get(
                    "canonical_smiles"
                )

                df.loc[
                    index,
                    "ChEMBL_StandardInChI"
                ] = structures.get(
                    "standard_inchi"
                )

                df.loc[
                    index,
                    "ChEMBL_StandardInChIKey"
                ] = structures.get(
                    "standard_inchi_key"
                )

                df.loc[
                    index,
                    "ChEMBL_Status"
                ] = "OK"

                print(
                    "  -> 재시도 성공:",
                    molecule.get(
                        "molecule_chembl_id"
                    )
                )

            else:

                df.loc[
                    index,
                    "ChEMBL_Status"
                ] = "NOT_FOUND"

                print(
                    "  -> ChEMBL 미등록"
                )

        else:

            df.loc[
                index,
                "ChEMBL_Status"
            ] = (
                "HTTP_" +
                str(response.status_code)
            )

            print(
                "  -> HTTP",
                response.status_code
            )

    except Exception as e:

        df.loc[
            index,
            "ChEMBL_Status"
        ] = "ERROR"

        print(
            "  -> 오류:",
            e
        )

    time.sleep(1.0)


# 결과 저장
df.to_csv(
    OUTPUT_FILE,
    index=False,
    encoding="utf-8-sig"
)


print()
print("================================")
print("ChEMBL 오류 재시도 완료")
print("================================")

print(
    "전체 데이터:",
    len(df)
)

print(
    "ChEMBL 연결 성공:",
    (
        df["ChEMBL_Status"]
        == "OK"
    ).sum()
)

print(
    "ChEMBL 미등록:",
    (
        df["ChEMBL_Status"]
        == "NOT_FOUND"
    ).sum()
)

print(
    "ERROR:",
    (
        df["ChEMBL_Status"]
        == "ERROR"
    ).sum()
)

print(
    "HTTP 오류:",
    (
        df["ChEMBL_Status"]
        .astype(str)
        .str.startswith("HTTP_")
    ).sum()
)

print()
print(
    "저장 파일:",
    OUTPUT_FILE
)