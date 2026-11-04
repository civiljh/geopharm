import pandas as pd
from pathlib import Path


# ============================================================
# GeoPharm Plant Validator
# ------------------------------------------------------------
# 기존 분석 프로그램을 수정하지 않고,
# 현재 식물 데이터가 각 단계에 얼마나 준비되어 있는지 검사한다.
#
# 검사 단계:
# 1. 식물 등록
# 2. KNApSAcK
# 3. PubChem
# 4. ChEMBL
# 5. AI 연결
# 6. AI 예측
#
# 이 프로그램은 외부 API를 새로 호출하지 않는다.
# 기존 CSV 파일만 읽어서 현재 상태를 검사한다.
# ============================================================


# ------------------------------------------------------------
# 파일 위치
# ------------------------------------------------------------

PLANT_FILE = Path("data/raw/medicinal_plants.csv")
KNAPSACK_FILE = Path("data/raw/plant_compounds.csv")
PUBCHEM_FILE = Path("data/raw/plant_compounds_pubchem.csv")
CHEMBL_FILE = Path("data/processed/plant_compounds_chembl.csv")
AI_CONNECTION_FILE = Path("data/processed/plant_ai_connection.csv")
AI_PREDICTION_FILE = Path("data/processed/plant_ai_predictions.csv")

OUTPUT_FILE = Path("data/processed/plant_validation_report.csv")


# ------------------------------------------------------------
# 기본 함수
# ------------------------------------------------------------

def load_csv(path):
    """CSV 파일을 읽는다."""
    if not path.exists():
        return None

    try:
        return pd.read_csv(path)
    except Exception as e:
        print(f"[오류] 파일 읽기 실패: {path}")
        print(f"       {e}")
        return None


def normalize_id(value):
    """Plant_ID를 안전하게 문자열로 변환한다."""
    if pd.isna(value):
        return ""

    return str(value).strip()


def get_plant_ids(df):
    """DataFrame에서 Plant_ID 집합을 만든다."""
    if df is None:
        return set()

    if "Plant_ID" not in df.columns:
        return set()

    return set(
        df["Plant_ID"]
        .dropna()
        .astype(str)
        .str.strip()
        .unique()
    )


def count_rows_for_plant(df, plant_id):
    """특정 식물의 데이터 행 수를 반환한다."""
    if df is None:
        return 0

    if "Plant_ID" not in df.columns:
        return 0

    return int(
        (
            df["Plant_ID"]
            .fillna("")
            .astype(str)
            .str.strip()
            == plant_id
        ).sum()
    )


def count_unique_for_plant(df, plant_id, column):
    """특정 식물의 고유 값 개수를 반환한다."""
    if df is None:
        return 0

    if "Plant_ID" not in df.columns:
        return 0

    if column not in df.columns:
        return 0

    selected = df[
        df["Plant_ID"]
        .fillna("")
        .astype(str)
        .str.strip()
        == plant_id
    ]

    return int(
        selected[column]
        .dropna()
        .astype(str)
        .str.strip()
        .replace("", pd.NA)
        .dropna()
        .nunique()
    )


def get_status(df, plant_id, value_column=None):
    """
    특정 식물의 데이터 존재 여부를 판단한다.

    반환:
    - NO_FILE
    - NO_DATA
    - DATA
    """

    if df is None:
        return "NO_FILE"

    if "Plant_ID" not in df.columns:
        return "NO_FILE"

    selected = df[
        df["Plant_ID"]
        .fillna("")
        .astype(str)
        .str.strip()
        == plant_id
    ]

    if len(selected) == 0:
        return "NO_DATA"

    if value_column is not None:

        if value_column not in selected.columns:
            return "NO_FILE"

        valid = (
            selected[value_column]
            .notna()
            & (
                selected[value_column]
                .astype(str)
                .str.strip()
                != ""
            )
        )

        if valid.sum() == 0:
            return "NO_DATA"

    return "DATA"


def final_ai_status(ai_prediction_status):
    """
    최종 AI 분석 가능 여부.

    실제 AI 예측 데이터가 존재하는 경우에만 YES.
    """

    if ai_prediction_status == "DATA":
        return "YES"

    if ai_prediction_status == "NO_FILE":
        return "NO_FILE"

    return "NO"


# ------------------------------------------------------------
# 시작
# ------------------------------------------------------------

print()
print("============================================================")
print("GeoPharm 식물 데이터 자동 검증")
print("============================================================")
print()


# ------------------------------------------------------------
# 1. 식물 등록 파일 읽기
# ------------------------------------------------------------

plants = load_csv(PLANT_FILE)

if plants is None:
    print("[중단]")
    print(f"식물 등록 파일을 찾을 수 없습니다: {PLANT_FILE}")
    raise SystemExit(1)


required_plant_columns = [
    "Plant_ID",
    "Scientific_Name"
]

missing_columns = [
    column
    for column in required_plant_columns
    if column not in plants.columns
]

if missing_columns:

    print("[중단]")
    print("식물 등록 파일에 필요한 컬럼이 없습니다:")
    print(missing_columns)
    raise SystemExit(1)


plants = plants.copy()

plants["Plant_ID"] = (
    plants["Plant_ID"]
    .fillna("")
    .astype(str)
    .str.strip()
)

plants["Scientific_Name"] = (
    plants["Scientific_Name"]
    .fillna("")
    .astype(str)
    .str.strip()
)


# ------------------------------------------------------------
# 2. 각 단계의 기존 결과 읽기
# ------------------------------------------------------------

knapsack = load_csv(KNAPSACK_FILE)
pubchem = load_csv(PUBCHEM_FILE)
chembl = load_csv(CHEMBL_FILE)
ai_connection = load_csv(AI_CONNECTION_FILE)
ai_prediction = load_csv(AI_PREDICTION_FILE)


# ------------------------------------------------------------
# 3. 현재 식물 ID 집합
# ------------------------------------------------------------

plant_ids = set(
    plants["Plant_ID"]
    .dropna()
    .astype(str)
    .str.strip()
)

knapsack_ids = get_plant_ids(knapsack)
pubchem_ids = get_plant_ids(pubchem)
chembl_ids = get_plant_ids(chembl)
ai_connection_ids = get_plant_ids(ai_connection)
ai_prediction_ids = get_plant_ids(ai_prediction)


# ------------------------------------------------------------
# 4. 전체 단계 요약
# ------------------------------------------------------------

print("현재 식물 등록 수:", len(plant_ids))
print()

print("단계별 현재 데이터")
print("------------------------------------------------------------")
print(f"식물 등록 : {len(plant_ids)}개")
print(f"KNApSAcK : {len(knapsack_ids)}개")
print(f"PubChem  : {len(pubchem_ids)}개")
print(f"ChEMBL   : {len(chembl_ids)}개")
print(f"AI 연결  : {len(ai_connection_ids)}개")
print(f"AI 예측  : {len(ai_prediction_ids)}개")
print("------------------------------------------------------------")
print()


# ------------------------------------------------------------
# 5. 식물별 검증
# ------------------------------------------------------------

report_rows = []


for _, plant_row in plants.iterrows():

    plant_id = normalize_id(
        plant_row["Plant_ID"]
    )

    korean_name = ""

    if "Korean_Name" in plants.columns:
        korean_name = normalize_id(
            plant_row["Korean_Name"]
        )

    english_name = ""

    if "English_Name" in plants.columns:
        english_name = normalize_id(
            plant_row["English_Name"]
        )

    scientific_name = normalize_id(
        plant_row["Scientific_Name"]
    )

    # --------------------------------------------------------
    # KNApSAcK
    # --------------------------------------------------------

    knapsack_status = get_status(
        knapsack,
        plant_id
    )

    knapsack_compounds = count_unique_for_plant(
        knapsack,
        plant_id,
        "KNApSAcK_ID"
    )

    if knapsack_compounds == 0:
        knapsack_compounds = count_rows_for_plant(
            knapsack,
            plant_id
        )


    # --------------------------------------------------------
    # PubChem
    # --------------------------------------------------------

    pubchem_status = get_status(
        pubchem,
        plant_id,
        "PubChem_Status"
    )

    pubchem_compounds = 0

    if pubchem is not None and "Plant_ID" in pubchem.columns:

        selected = pubchem[
            pubchem["Plant_ID"]
            .fillna("")
            .astype(str)
            .str.strip()
            == plant_id
        ]

        if "PubChem_Status" in selected.columns:

            selected_ok = selected[
                selected["PubChem_Status"]
                .fillna("")
                .astype(str)
                .str.strip()
                == "OK"
            ]

            if "Compound_Name" in selected_ok.columns:

                pubchem_compounds = int(
                    selected_ok["Compound_Name"]
                    .dropna()
                    .astype(str)
                    .str.strip()
                    .replace("", pd.NA)
                    .dropna()
                    .nunique()
                )

            else:
                pubchem_compounds = len(selected_ok)


    # --------------------------------------------------------
    # ChEMBL
    # --------------------------------------------------------

    chembl_status = get_status(
        chembl,
        plant_id,
        "ChEMBL_Status"
    )

    chembl_compounds = 0

    if chembl is not None and "Plant_ID" in chembl.columns:

        selected = chembl[
            chembl["Plant_ID"]
            .fillna("")
            .astype(str)
            .str.strip()
            == plant_id
        ]

        if "ChEMBL_Status" in selected.columns:

            selected_ok = selected[
                selected["ChEMBL_Status"]
                .fillna("")
                .astype(str)
                .str.strip()
                == "OK"
            ]

            if "ChEMBL_ID" in selected_ok.columns:

                chembl_compounds = int(
                    selected_ok["ChEMBL_ID"]
                    .dropna()
                    .astype(str)
                    .str.strip()
                    .replace("", pd.NA)
                    .dropna()
                    .nunique()
                )


    # --------------------------------------------------------
    # AI 연결
    # --------------------------------------------------------

    ai_connection_status = get_status(
        ai_connection,
        plant_id,
        "ChEMBL_ID"
    )

    ai_connection_compounds = count_unique_for_plant(
        ai_connection,
        plant_id,
        "ChEMBL_ID"
    )


    # --------------------------------------------------------
    # AI 예측
    # --------------------------------------------------------

    ai_prediction_status = get_status(
        ai_prediction,
        plant_id,
        "Predicted_pChEMBL"
    )

    ai_prediction_compounds = count_unique_for_plant(
        ai_prediction,
        plant_id,
        "ChEMBL_ID"
    )


    # --------------------------------------------------------
    # 최종 AI 분석 가능 여부
    # --------------------------------------------------------

    final_status = final_ai_status(
        ai_prediction_status
    )


    # --------------------------------------------------------
    # 데이터 버전 상태
    # --------------------------------------------------------

    stage_statuses = [
        knapsack_status,
        pubchem_status,
        chembl_status,
        ai_connection_status,
        ai_prediction_status
    ]

    if "NO_FILE" in stage_statuses:
        overall_status = "DATA_FILE_MISSING"

    elif ai_prediction_status == "DATA":
        overall_status = "AI_ANALYSIS_READY"

    elif knapsack_status == "NO_DATA":
        overall_status = "KNAPSACK_NO_DATA"

    elif pubchem_status == "NO_DATA":
        overall_status = "PUBCHEM_NOT_READY"

    elif chembl_status == "NO_DATA":
        overall_status = "CHEMBL_NOT_READY"

    elif ai_connection_status == "NO_DATA":
        overall_status = "AI_CONNECTION_NOT_READY"

    elif ai_prediction_status == "NO_DATA":
        overall_status = "AI_PREDICTION_NOT_READY"

    else:
        overall_status = "CHECK_REQUIRED"


    # --------------------------------------------------------
    # 결과 저장
    # --------------------------------------------------------

    report_rows.append(
        {
            "Plant_ID": plant_id,
            "Korean_Name": korean_name,
            "English_Name": english_name,
            "Scientific_Name": scientific_name,

            "Plant_Registered": "YES",

            "KNApSAcK_Status": knapsack_status,
            "PubChem_Status": pubchem_status,
            "ChEMBL_Status": chembl_status,
            "AI_Connection_Status": ai_connection_status,
            "AI_Prediction_Status": ai_prediction_status,

            "KNApSAcK_Compound_Count": knapsack_compounds,
            "PubChem_Compound_Count": pubchem_compounds,
            "ChEMBL_Compound_Count": chembl_compounds,
            "AI_Connection_Compound_Count": ai_connection_compounds,
            "AI_Prediction_Compound_Count": ai_prediction_compounds,

            "Final_AI_Analysis": final_status,
            "Overall_Status": overall_status
        }
    )


# ------------------------------------------------------------
# 6. 검증 결과 DataFrame
# ------------------------------------------------------------

report = pd.DataFrame(
    report_rows
)


# ------------------------------------------------------------
# 7. 결과 저장
# ------------------------------------------------------------

OUTPUT_FILE.parent.mkdir(
    parents=True,
    exist_ok=True
)

report.to_csv(
    OUTPUT_FILE,
    index=False,
    encoding="utf-8-sig"
)


# ------------------------------------------------------------
# 8. 콘솔 요약
# ------------------------------------------------------------

print("============================================================")
print("식물별 검증 결과")
print("============================================================")

display_columns = [
    "Plant_ID",
    "Scientific_Name",
    "KNApSAcK_Status",
    "PubChem_Status",
    "ChEMBL_Status",
    "AI_Connection_Status",
    "AI_Prediction_Status",
    "Final_AI_Analysis",
    "Overall_Status"
]

print(
    report[display_columns]
    .to_string(index=False)
)

print()
print("============================================================")
print("전체 검증 요약")
print("============================================================")

print(
    "전체 식물:",
    len(report)
)

print(
    "KNApSAcK 데이터 있음:",
    (
        report["KNApSAcK_Status"]
        == "DATA"
    ).sum()
)

print(
    "KNApSAcK 데이터 없음:",
    (
        report["KNApSAcK_Status"]
        == "NO_DATA"
    ).sum()
)

print(
    "PubChem 데이터 있음:",
    (
        report["PubChem_Status"]
        == "DATA"
    ).sum()
)

print(
    "ChEMBL 데이터 있음:",
    (
        report["ChEMBL_Status"]
        == "DATA"
    ).sum()
)

print(
    "AI 연결 데이터 있음:",
    (
        report["AI_Connection_Status"]
        == "DATA"
    ).sum()
)

print(
    "AI 예측 데이터 있음:",
    (
        report["AI_Prediction_Status"]
        == "DATA"
    ).sum()
)

print(
    "최종 AI 분석 가능:",
    (
        report["Final_AI_Analysis"]
        == "YES"
    ).sum()
)

print()
print("전체 상태별 개수")
print(
    report["Overall_Status"]
    .value_counts()
    .to_string()
)

print()
print("============================================================")
print("검증 완료")
print("============================================================")
print()
print("검증 보고서:")
print(OUTPUT_FILE)