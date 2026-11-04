import pandas as pd
import requests
import time

INPUT_FILE = "data/raw/plant_compounds_pubchem.csv"
OUTPUT_FILE = "data/processed/plant_compounds_chembl.csv"

df = pd.read_csv(INPUT_FILE)

print("전체 식물 성분:", len(df))
print()

session = requests.Session()

results = []

for number, (_, row) in enumerate(df.iterrows(), start=1):

    inchikey = row["InChIKey"]

    print(
        f"[{number}/{len(df)}] "
        f"{row['Plant_ID']} | "
        f"{row['Compound_Name']}"
    )

    chembl_id = None
    pref_name = None
    molecular_formula = None
    molecular_weight = None
    alogp = None
    hba = None
    hbd = None
    psa = None
    qed = None
    canonical_smiles = None
    standard_inchi = None
    standard_inchi_key = None
    status = "FAIL"

    if pd.isna(inchikey) or str(inchikey).strip() == "":
        status = "NO_INCHIKEY"

        print("  -> InChIKey 없음")

    else:

        inchikey = str(inchikey).strip()

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
                timeout=20
            )

            if response.status_code == 200:

                data = response.json()

                molecules = data.get(
                    "molecules",
                    []
                )

                if len(molecules) > 0:

                    molecule = molecules[0]

                    chembl_id = molecule.get(
                        "molecule_chembl_id"
                    )

                    pref_name = molecule.get(
                        "pref_name"
                    )

                    properties = (
                        molecule.get(
                            "molecule_properties"
                        )
                        or {}
                    )

                    molecular_formula = (
                        properties.get(
                            "full_molformula"
                        )
                    )

                    molecular_weight = (
                        properties.get(
                            "full_mwt"
                        )
                    )

                    alogp = properties.get(
                        "alogp"
                    )

                    hba = properties.get(
                        "hba"
                    )

                    hbd = properties.get(
                        "hbd"
                    )

                    psa = properties.get(
                        "psa"
                    )

                    qed = properties.get(
                        "qed_weighted"
                    )

                    structures = (
                        molecule.get(
                            "molecule_structures"
                        )
                        or {}
                    )

                    canonical_smiles = (
                        structures.get(
                            "canonical_smiles"
                        )
                    )

                    standard_inchi = (
                        structures.get(
                            "standard_inchi"
                        )
                    )

                    standard_inchi_key = (
                        structures.get(
                            "standard_inchi_key"
                        )
                    )

                    status = "OK"

                    print(
                        "  ->",
                        chembl_id,
                        "|",
                        pref_name
                    )

                else:

                    status = "NOT_FOUND"

                    print(
                        "  -> ChEMBL 검색 결과 없음"
                    )

            else:

                status = (
                    "HTTP_"
                    + str(response.status_code)
                )

                print(
                    "  -> HTTP",
                    response.status_code
                )

        except Exception as e:

            status = "ERROR"

            print(
                "  -> 오류:",
                e
            )

    results.append(
        {
            "ChEMBL_ID": chembl_id,
            "ChEMBL_Name": pref_name,
            "ChEMBL_MolecularFormula": molecular_formula,
            "ChEMBL_MolecularWeight": molecular_weight,
            "ChEMBL_AlogP": alogp,
            "ChEMBL_HBA": hba,
            "ChEMBL_HBD": hbd,
            "ChEMBL_PSA": psa,
            "ChEMBL_QED": qed,
            "ChEMBL_CanonicalSMILES": canonical_smiles,
            "ChEMBL_StandardInChI": standard_inchi,
            "ChEMBL_StandardInChIKey": standard_inchi_key,
            "ChEMBL_Status": status,
        }
    )

    time.sleep(0.3)


chembl_df = pd.DataFrame(results)

final_df = pd.concat(
    [
        df.reset_index(drop=True),
        chembl_df
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
print("ChEMBL 연결 완료")
print("================================")

print(
    "전체 성분:",
    len(final_df)
)

print(
    "ChEMBL 연결 성공:",
    (
        final_df["ChEMBL_Status"]
        == "OK"
    ).sum()
)

print(
    "ChEMBL 검색 결과 없음:",
    (
        final_df["ChEMBL_Status"]
        == "NOT_FOUND"
    ).sum()
)

print(
    "InChIKey 없음:",
    (
        final_df["ChEMBL_Status"]
        == "NO_INCHIKEY"
    ).sum()
)

print(
    "기타 오류:",
    (
        ~final_df["ChEMBL_Status"].isin(
            [
                "OK",
                "NOT_FOUND",
                "NO_INCHIKEY"
            ]
        )
    ).sum()
)

print()
print("저장 파일:", OUTPUT_FILE)