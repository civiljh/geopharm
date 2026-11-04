import sqlite3


DB_FILE = "data/processed/geopharm_basic.db"


print("========================================")
print("GeoPharm 기본 데이터베이스 무결성 검사")
print("========================================")


# ==================================================
# 데이터베이스 연결
# ==================================================

conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()


# ==================================================
# 1. 테이블 존재 여부 확인
# ==================================================

required_tables = [
    "plants",
    "plant_compounds",
    "pubchem_compounds",
    "chembl_compounds",
    "uniprot_proteins",
    "ai_predictions",
    "database_metadata"
]


print()
print("========================================")
print("1. 테이블 검사")
print("========================================")


cursor.execute(
    """
    SELECT name
    FROM sqlite_master
    WHERE type='table'
    """
)

existing_tables = {
    row[0]
    for row in cursor.fetchall()
}


for table in required_tables:

    if table in existing_tables:
        print(
            f"[OK] {table}"
        )
    else:
        print(
            f"[FAIL] {table}"
        )


# ==================================================
# 2. 각 테이블 행 수
# ==================================================

print()
print("========================================")
print("2. 데이터 행 수")
print("========================================")


for table in required_tables:

    if table not in existing_tables:
        continue

    cursor.execute(
        f'SELECT COUNT(*) FROM "{table}"'
    )

    count = cursor.fetchone()[0]

    print(
        f"{table}: {count}행"
    )


# ==================================================
# 3. Plant_ID 연결 검사
# ==================================================

print()
print("========================================")
print("3. AI → 식물 연결 검사")
print("========================================")


cursor.execute(
    """
    SELECT COUNT(*)
    FROM ai_predictions a
    LEFT JOIN plants p
        ON a.Plant_ID = p.Plant_ID
    WHERE p.Plant_ID IS NULL
    """
)

missing_plants = cursor.fetchone()[0]

print(
    "식물 정보가 없는 AI 예측:",
    missing_plants
)


# ==================================================
# 4. ChEMBL 연결 검사
# ==================================================

print()
print("========================================")
print("4. AI → 식물화합물 연결 검사")
print("========================================")


cursor.execute(
    """
    SELECT COUNT(*)
    FROM ai_predictions a
    LEFT JOIN plant_compounds pc
        ON a.Plant_ID = pc.Plant_ID
        AND a.ChEMBL_ID = pc.ChEMBL_ID
    WHERE pc.ChEMBL_ID IS NULL
    """
)

missing_compounds = cursor.fetchone()[0]

print(
    "식물-화합물 정보가 없는 AI 예측:",
    missing_compounds
)


# ==================================================
# 5. UniProt 연결 검사
# ==================================================

print()
print("========================================")
print("5. AI → UniProt 연결 검사")
print("========================================")


cursor.execute(
    """
    SELECT COUNT(*)
    FROM ai_predictions a
    LEFT JOIN uniprot_proteins u
        ON a.UniProt_ID = u.UniProt_ID
    WHERE u.UniProt_ID IS NULL
    """
)

missing_uniprot = cursor.fetchone()[0]

print(
    "UniProt 정보가 없는 AI 예측:",
    missing_uniprot
)


# ==================================================
# 6. AI 예측값 NULL 검사
# ==================================================

print()
print("========================================")
print("6. AI 예측값 검사")
print("========================================")


cursor.execute(
    """
    SELECT COUNT(*)
    FROM ai_predictions
    WHERE Predicted_pChEMBL IS NULL
    """
)

missing_predictions = cursor.fetchone()[0]

print(
    "AI 예측값이 없는 행:",
    missing_predictions
)


# ==================================================
# 7. 기본 식물 ID 중복 검사
# ==================================================

print()
print("========================================")
print("7. 식물 ID 중복 검사")
print("========================================")


cursor.execute(
    """
    SELECT Plant_ID, COUNT(*)
    FROM plants
    GROUP BY Plant_ID
    HAVING COUNT(*) > 1
    """
)

duplicate_plants = cursor.fetchall()

print(
    "중복 Plant_ID:",
    len(duplicate_plants)
)


# ==================================================
# 8. AI 예측 기본 통계
# ==================================================

print()
print("========================================")
print("8. AI 예측 기본 통계")
print("========================================")


cursor.execute(
    """
    SELECT
        COUNT(*),
        COUNT(DISTINCT Plant_ID),
        COUNT(DISTINCT ChEMBL_ID),
        COUNT(DISTINCT UniProt_ID),
        MIN(Predicted_pChEMBL),
        MAX(Predicted_pChEMBL)
    FROM ai_predictions
    """
)

stats = cursor.fetchone()

print(
    "전체 예측:",
    stats[0]
)

print(
    "식물:",
    stats[1]
)

print(
    "화합물:",
    stats[2]
)

print(
    "UniProt:",
    stats[3]
)

print(
    "최소 Predicted_pChEMBL:",
    stats[4]
)

print(
    "최대 Predicted_pChEMBL:",
    stats[5]
)


# ==================================================
# 9. 데이터베이스 메타정보
# ==================================================

print()
print("========================================")
print("9. 데이터베이스 메타정보")
print("========================================")


cursor.execute(
    """
    SELECT
        Database_Name,
        Version,
        Disease_Data_Included,
        AI_Prediction_Included
    FROM database_metadata
    """
)

metadata = cursor.fetchone()

if metadata:

    print(
        "Database:",
        metadata[0]
    )

    print(
        "Version:",
        metadata[1]
    )

    print(
        "Disease Data:",
        metadata[2]
    )

    print(
        "AI Prediction:",
        metadata[3]
    )


# ==================================================
# 10. 최종 판정
# ==================================================

print()
print("========================================")
print("10. 최종 검사")
print("========================================")


checks = {
    "필수 테이블": all(
        table in existing_tables
        for table in required_tables
    ),

    "식물 연결": missing_plants == 0,

    "화합물 연결": missing_compounds == 0,

    "UniProt 연결": missing_uniprot == 0,

    "AI 예측값": missing_predictions == 0,

    "Plant_ID 중복": len(duplicate_plants) == 0
}


all_ok = all(checks.values())


for name, result in checks.items():

    if result:
        print(
            f"[OK] {name}"
        )
    else:
        print(
            f"[FAIL] {name}"
        )


print()

if all_ok:

    print(
        "기본 데이터베이스 무결성 검사: PASS"
    )

else:

    print(
        "기본 데이터베이스 무결성 검사: CHECK REQUIRED"
    )


# ==================================================
# 종료
# ==================================================

conn.close()


print()
print("========================================")
print("검사 완료")
print("========================================")