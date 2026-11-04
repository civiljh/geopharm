import sqlite3
import pandas as pd
from pathlib import Path


# ==================================================
# 파일 경로
# ==================================================

DB_FILE = "data/processed/geopharm_basic.db"

PLANT_FILE = "data/raw/medicinal_plants.csv"
PLANT_COMPOUND_FILE = "data/processed/plant_compounds_chembl.csv"
PUBCHEM_FILE = "data/raw/plant_compounds_pubchem.csv"
CHEMBL_FILE = "data/processed/plant_compounds_chembl.csv"
UNIPROT_FILE = "data/processed/uniprot_details.csv"
AI_FILE = "data/processed/plant_ai_annotated.csv"


# ==================================================
# 데이터베이스 폴더 확인
# ==================================================

Path("data/processed").mkdir(
    parents=True,
    exist_ok=True
)


# ==================================================
# 기존 DB가 있으면 삭제하지 않고 중단
# ==================================================

if Path(DB_FILE).exists():

    raise SystemExit(
        "기존 데이터베이스가 이미 존재합니다. "
        "안전을 위해 기존 DB를 덮어쓰지 않습니다."
    )


print("========================================")
print("GeoPharm 기본 데이터베이스 구축")
print("========================================")


# ==================================================
# CSV 불러오기
# ==================================================

print()
print("데이터를 불러오는 중...")


plants = pd.read_csv(
    PLANT_FILE
)

plant_compounds = pd.read_csv(
    PLANT_COMPOUND_FILE
)

pubchem = pd.read_csv(
    PUBCHEM_FILE
)

chembl = pd.read_csv(
    CHEMBL_FILE
)

uniprot = pd.read_csv(
    UNIPROT_FILE
)

ai = pd.read_csv(
    AI_FILE
)


print()
print("불러오기 완료")

print(
    "식물:",
    len(plants)
)

print(
    "식물-화합물:",
    len(plant_compounds)
)

print(
    "PubChem:",
    len(pubchem)
)

print(
    "ChEMBL:",
    len(chembl)
)

print(
    "UniProt:",
    len(uniprot)
)

print(
    "AI 예측:",
    len(ai)
)


# ==================================================
# SQLite 연결
# ==================================================

print()
print("SQLite 데이터베이스 생성 중...")


conn = sqlite3.connect(
    DB_FILE
)


# ==================================================
# 1. plants
# ==================================================

plants_table = plants[
    [
        "Plant_ID",
        "Common_Name_KO",
        "English_Name",
        "Scientific_Name"
    ]
].drop_duplicates(
    subset=["Plant_ID"]
)


plants_table.to_sql(
    "plants",
    conn,
    if_exists="replace",
    index=False
)


# ==================================================
# 2. plant_compounds
# ==================================================

plant_compound_columns = [
    "Plant_ID",
    "KNApSAcK_ID",
    "CAS",
    "Compound_Name",
    "Molecular_Formula",
    "Molecular_Weight",
    "Scientific_Name",
    "PubChem_CID",
    "PubChem_Title",
    "PubChem_SMILES",
    "InChIKey",
    "PubChem_Status",
    "ChEMBL_ID",
    "ChEMBL_Name",
    "ChEMBL_MolecularFormula",
    "ChEMBL_MolecularWeight",
    "ChEMBL_AlogP",
    "ChEMBL_HBA",
    "ChEMBL_HBD",
    "ChEMBL_PSA",
    "ChEMBL_QED",
    "ChEMBL_CanonicalSMILES",
    "ChEMBL_StandardInChI",
    "ChEMBL_StandardInChIKey",
    "ChEMBL_Status"
]


available_columns = [
    column
    for column in plant_compound_columns
    if column in plant_compounds.columns
]


plant_compounds_table = (
    plant_compounds[
        available_columns
    ]
    .drop_duplicates()
)


plant_compounds_table.to_sql(
    "plant_compounds",
    conn,
    if_exists="replace",
    index=False
)


# ==================================================
# 3. pubchem
# ==================================================

pubchem_table = pubchem.copy()

pubchem_table.to_sql(
    "pubchem_compounds",
    conn,
    if_exists="replace",
    index=False
)


# ==================================================
# 4. chembl
# ==================================================

chembl_table = chembl.copy()

chembl_table.to_sql(
    "chembl_compounds",
    conn,
    if_exists="replace",
    index=False
)


# ==================================================
# 5. uniprot
# ==================================================

uniprot_table = uniprot.copy()

uniprot_table.to_sql(
    "uniprot_proteins",
    conn,
    if_exists="replace",
    index=False
)


# ==================================================
# 6. AI predictions
# ==================================================

ai_table = ai.copy()

ai_table.to_sql(
    "ai_predictions",
    conn,
    if_exists="replace",
    index=False
)


# ==================================================
# 7. 데이터베이스 메타정보
# ==================================================

metadata = pd.DataFrame(
    [
        {
            "Database_Name": "GeoPharm Basic Database",
            "Version": "1.0",
            "Disease_Data_Included": False,
            "AI_Prediction_Included": True
        }
    ]
)


metadata.to_sql(
    "database_metadata",
    conn,
    if_exists="replace",
    index=False
)


# ==================================================
# 저장
# ==================================================

conn.commit()


# ==================================================
# 테이블 확인
# ==================================================

cursor = conn.cursor()

cursor.execute(
    """
    SELECT name
    FROM sqlite_master
    WHERE type='table'
    ORDER BY name
    """
)

tables = cursor.fetchall()


print()
print("========================================")
print("데이터베이스 테이블")
print("========================================")

for table in tables:

    print(
        table[0]
    )


# ==================================================
# 각 테이블 행 수 확인
# ==================================================

print()
print("========================================")
print("테이블 데이터 확인")
print("========================================")


for table in tables:

    table_name = table[0]

    cursor.execute(
        f'SELECT COUNT(*) FROM "{table_name}"'
    )

    count = cursor.fetchone()[0]

    print(
        f"{table_name}: {count}행"
    )


# ==================================================
# 종료
# ==================================================

conn.close()


print()
print("========================================")
print("기본 데이터베이스 구축 완료")
print("========================================")

print(
    "파일:",
    DB_FILE
)

print()
print("주의:")
print("현재 데이터베이스에는 질병 정보가 없습니다.")
print("질병 분석은 기본 데이터베이스 검증 후 별도로 추가합니다.")