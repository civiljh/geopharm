import pandas as pd
import requests


INPUT_FILE = "data/processed/plant_compounds_chembl.csv"
OUTPUT_FILE = "data/processed/plant_compounds_chembl.csv"


df = pd.read_csv(INPUT_FILE)


# 복구할 ChEMBL ID
fixes = {
    "VHYFNPMBLIVWCW-UHFFFAOYSA-N": "CHEMBL3561645",
    "QOXUIQMPPDIDGM-PMOUVXMZSA-N": "CHEMBL470270",
    "KDCGOANMDULRCW-UHFFFAOYSA-N": "CHEMBL302239",
}


print("전체 데이터:", len(df))
print("복구 대상:", len(fixes))
print()


session = requests.Session()


for inchikey, chembl_id in fixes.items():

    print("처리:", chembl_id, "|", inchikey)

    response = session.get(
        "https://www.ebi.ac.uk/chembl/api/data/molecule/"
        + chembl_id
        + ".json",
        timeout=30
    )

    response.raise_for_status()

    molecule = response.json()

    # Chemical_InChIKey가 일치하는 행 찾기
    mask = (
        df["Chemical_InChIKey"]
        .astype(str)
        .str.strip()
        == inchikey
    )

    if mask.sum() == 0:
        print("  -> 해당 InChIKey 행을 찾지 못함")
        continue

    properties = (
        molecule.get("molecule_properties")
        or {}
    )

    structures = (
        molecule.get("molecule_structures")
        or {}
    )

    # 기본 정보
    df.loc[mask, "ChEMBL_ID"] = molecule.get(
        "molecule_chembl_id"
    )

    df.loc[mask, "ChEMBL_Name"] = molecule.get(
        "pref_name"
    )

    # 분자 특성
    # ChEMBL API는 숫자 값을 문자열로 반환할 수 있으므로
    # pandas에 저장하기 전에 float으로 변환
    molecular_weight = properties.get(
        "full_mwt"
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

    df.loc[mask, "ChEMBL_MolecularFormula"] = (
        properties.get("full_molformula")
    )

    if molecular_weight is not None:
        df.loc[mask, "ChEMBL_MolecularWeight"] = float(
            molecular_weight
        )

    if alogp is not None:
        df.loc[mask, "ChEMBL_AlogP"] = float(
            alogp
        )

    if hba is not None:
        df.loc[mask, "ChEMBL_HBA"] = float(
            hba
        )

    if hbd is not None:
        df.loc[mask, "ChEMBL_HBD"] = float(
            hbd
        )

    if psa is not None:
        df.loc[mask, "ChEMBL_PSA"] = float(
            psa
        )

    if qed is not None:
        df.loc[mask, "ChEMBL_QED"] = float(
            qed
        )

    # 구조 정보
    df.loc[mask, "ChEMBL_CanonicalSMILES"] = (
        structures.get("canonical_smiles")
    )

    df.loc[mask, "ChEMBL_StandardInChI"] = (
        structures.get("standard_inchi")
    )

    df.loc[mask, "ChEMBL_StandardInChIKey"] = (
        structures.get("standard_inchi_key")
    )

    # 상태 변경
    df.loc[mask, "ChEMBL_Status"] = "OK"

    print(
        "  -> 복구 성공:",
        molecule.get("molecule_chembl_id"),
        "|",
        molecule.get("pref_name")
    )


# 저장
df.to_csv(
    OUTPUT_FILE,
    index=False,
    encoding="utf-8-sig"
)


print()
print("================================")
print("ChEMBL 오류 데이터 최종 복구 완료")
print("================================")

print(
    "전체 데이터:",
    len(df)
)

print(
    "ChEMBL 연결 성공:",
    (df["ChEMBL_Status"] == "OK").sum()
)

print(
    "ChEMBL 미등록:",
    (df["ChEMBL_Status"] == "NOT_FOUND").sum()
)

print(
    "ERROR:",
    (df["ChEMBL_Status"] == "ERROR").sum()
)

print()
print("저장 파일:", OUTPUT_FILE)