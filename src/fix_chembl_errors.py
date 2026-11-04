import pandas as pd
import requests
import time


INPUT_FILE = "data/processed/plant_compounds_chembl.csv"
OUTPUT_FILE = "data/processed/plant_compounds_chembl.csv"


df = pd.read_csv(INPUT_FILE)


# 현재 ERROR 상태인 3개만 복구
target = df[
    df["ChEMBL_Status"] == "ERROR"
].copy()


print("전체 데이터:", len(df))
print("복구 대상:", len(target))
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

        response = session.get(
            "https://www.ebi.ac.uk/chembl/api/data/molecule.json",
            params={
                "molecule_structures__standard_inchi_key":
                    inchikey
            },
            timeout=30
        )

        response.raise_for_status()

        data = response.json()

        molecules = data.get(
            "molecules",
            []
        )

        if len(molecules) == 0:

            print(
                "  -> ChEMBL 레코드 없음"
            )

            df.loc[
                index,
                "ChEMBL_Status"
            ] = "NOT_FOUND"

            continue


        molecule = molecules[0]


        # 기본 정보
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


        # 분자 특성
        properties = (
            molecule.get(
                "molecule_properties"
            )
            or {}
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


        # 구조 정보
        structures = (
            molecule.get(
                "molecule_structures"
            )
            or {}
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
            "  -> 복구 성공:",
            molecule.get(
                "molecule_chembl_id"
            ),
            "|",
            molecule.get(
                "pref_name"
            )
        )


    except Exception as e:

        print(
            "  -> 오류:",
            e
        )


    time.sleep(1.0)


# 저장
df.to_csv(
    OUTPUT_FILE,
    index=False,
    encoding="utf-8-sig"
)


print()
print("================================")
print("ChEMBL 오류 데이터 복구 완료")
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

print()
print(
    "저장 파일:",
    OUTPUT_FILE
)