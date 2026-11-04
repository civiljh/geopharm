import os
import sys
import subprocess
import pandas as pd


BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

PLANT_FILE = os.path.join(
    BASE_DIR,
    "data",
    "raw",
    "medicinal_plants.csv"
)

EXTERNAL_FILE = os.path.join(
    BASE_DIR,
    "data",
    "raw",
    "external_plant_compounds.csv"
)


# ============================================================
# 공통 함수
# ============================================================

def run_script(script_name, input_text=None):

    script_path = os.path.join(
        BASE_DIR,
        "src",
        script_name
    )

    if not os.path.exists(script_path):

        print()
        print("ERROR: 프로그램 파일을 찾을 수 없습니다.")
        print(script_path)
        raise SystemExit(1)

    print()
    print("=" * 70)
    print("실행:", script_name)
    print("=" * 70)
    print()

    result = subprocess.run(
        [sys.executable, script_path],
        input=input_text,
        text=True,
        cwd=BASE_DIR
    )

    if result.returncode != 0:

        print()
        print("=" * 70)
        print("ERROR: 단계 실행 실패")
        print("=" * 70)
        print()
        print("실패한 프로그램:", script_name)

        raise SystemExit(result.returncode)

    print()
    print("완료:", script_name)


# ============================================================
# Plant_ID 찾기
# ============================================================

def find_registered_plant(scientific_name):

    if not os.path.exists(PLANT_FILE):

        print()
        print("ERROR: 약용식물 DB를 찾을 수 없습니다.")
        print(PLANT_FILE)

        raise SystemExit(1)

    plants = pd.read_csv(
        PLANT_FILE,
        encoding="utf-8-sig"
    )

    key = (
        str(scientific_name)
        .strip()
        .lower()
    )

    plants["_Scientific_Key"] = (
        plants["Scientific_Name"]
        .astype(str)
        .str.strip()
        .str.lower()
    )

    matched = plants[
        plants["_Scientific_Key"] == key
    ].copy()

    if matched.empty:
        return None

    return matched.iloc[0].to_dict()


# ============================================================
# KNApSAcK 결과에 실제 Plant_ID 연결
# ============================================================

def connect_real_plant_id(scientific_name):

    if not os.path.exists(EXTERNAL_FILE):

        print()
        print("ERROR: KNApSAcK 결과 파일이 없습니다.")
        print(EXTERNAL_FILE)

        raise SystemExit(1)

    plant = find_registered_plant(
        scientific_name
    )

    if plant is None:

        print()
        print("=" * 70)
        print("ERROR: 등록된 식물을 찾을 수 없습니다.")
        print("=" * 70)

        print()
        print("학명:", scientific_name)

        raise SystemExit(1)

    real_plant_id = str(
        plant["Plant_ID"]
    )

    compounds = pd.read_csv(
        EXTERNAL_FILE,
        encoding="utf-8-sig"
    )

    if "Scientific_Name" not in compounds.columns:

        print()
        print("ERROR: KNApSAcK 결과에 Scientific_Name이 없습니다.")

        raise SystemExit(1)

    compounds["_Scientific_Key"] = (
        compounds["Scientific_Name"]
        .astype(str)
        .str.strip()
        .str.lower()
    )

    key = (
        str(scientific_name)
        .strip()
        .lower()
    )

    matched = (
        compounds["_Scientific_Key"] == key
    )

    matched_count = int(
        matched.sum()
    )

    if matched_count == 0:

        print()
        print("=" * 70)
        print("ERROR: KNApSAcK 결과에서 해당 식물을 찾지 못했습니다.")
        print("=" * 70)

        print()
        print("학명:", scientific_name)

        raise SystemExit(1)

    compounds.loc[
        matched,
        "Plant_ID"
    ] = real_plant_id

    compounds.loc[
        matched,
        "Common_Name_KO"
    ] = plant.get(
        "Common_Name_KO",
        ""
    )

    compounds.loc[
        matched,
        "English_Name"
    ] = plant.get(
        "English_Name",
        ""
    )

    compounds.loc[
        matched,
        "Scientific_Name"
    ] = plant.get(
        "Scientific_Name",
        scientific_name
    )

    compounds = compounds.drop(
        columns=["_Scientific_Key"]
    )

    compounds.to_csv(
        EXTERNAL_FILE,
        index=False,
        encoding="utf-8-sig"
    )

    print()
    print("=" * 70)
    print("실제 Plant_ID 연결 완료")
    print("=" * 70)

    print()
    print("Plant_ID:", real_plant_id)
    print(
        "한국어 이름:",
        plant.get("Common_Name_KO", "")
    )
    print(
        "영어 이름:",
        plant.get("English_Name", "")
    )
    print(
        "학명:",
        plant.get("Scientific_Name", "")
    )
    print(
        "KNApSAcK 화합물:",
        matched_count
    )

    return real_plant_id


# ============================================================
# 메인
# ============================================================

def main(common_name_ko=None, english_name=None, scientific_name=None):

    print("=" * 70)
    print("GeoPharm - 새 약용식물 자동 분석")
    print("=" * 70)

    print()
    print("새 약용식물의 정보를 입력합니다.")
    print()

    if common_name_ko is None:
        common_name_ko = input(
            "한국어 이름: "
        ).strip()
    else:
        common_name_ko = str(common_name_ko).strip()

    if english_name is None:
        english_name = input(
            "영어 이름: "
        ).strip()
    else:
        english_name = str(english_name).strip()

    if scientific_name is None:
        scientific_name = input(
            "학명: "
        ).strip()
    else:
        scientific_name = str(scientific_name).strip()

    if not scientific_name:
            
        print()
        print("ERROR: 학명을 입력하지 않았습니다.")

        return

    print()
    print("=" * 70)
    print("입력 정보 확인")
    print("=" * 70)

    print()
    print("한국어 이름 :", common_name_ko)
    print("영어 이름   :", english_name)
    print("학명        :", scientific_name)

    # --------------------------------------------------------
    # 1. 기존 식물인지 먼저 확인
    # --------------------------------------------------------

    existing = find_registered_plant(
        scientific_name
    )

    if existing is not None:

        print()
        print("=" * 70)
        print("이미 등록된 식물입니다.")
        print("=" * 70)

        print()
        print(
            "Plant_ID:",
            existing.get("Plant_ID", "")
        )

        print(
            "한국어 이름:",
            existing.get("Common_Name_KO", "")
        )

        print(
            "영어 이름:",
            existing.get("English_Name", "")
        )

        print(
            "학명:",
            existing.get("Scientific_Name", "")
        )

        print()
        print("새 식물 등록을 중단합니다.")

        return

    # --------------------------------------------------------
    # 2. 식물 DB에 등록
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print("1단계 - 새 식물 등록")
    print("=" * 70)

    add_input = (
        common_name_ko + "\n" +
        english_name + "\n" +
        scientific_name + "\n"
    )

    run_script(
        "add_external_plant.py",
        add_input
    )

    # --------------------------------------------------------
    # 3. 실제 Plant_ID 확인
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print("2단계 - 실제 Plant_ID 확인")
    print("=" * 70)

    plant = find_registered_plant(
        scientific_name
    )

    if plant is None:

        print()
        print("ERROR: 등록 후 Plant_ID를 찾지 못했습니다.")

        return

    plant_id = str(
        plant["Plant_ID"]
    )

    print()
    print("실제 Plant_ID:", plant_id)

    # --------------------------------------------------------
    # 4. KNApSAcK 검색
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print("3단계 - KNApSAcK 화합물 검색")
    print("=" * 70)

    run_script(
        "external_plant_search.py",
        scientific_name + "\n"
    )

    # --------------------------------------------------------
    # 5. 실제 Plant_ID 연결
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print("4단계 - KNApSAcK 결과에 실제 Plant_ID 연결")
    print("=" * 70)

    connect_real_plant_id(
        scientific_name
    )

    # --------------------------------------------------------
    # 6. 새 식물 처리 대상 갱신
    # --------------------------------------------------------

    run_script(
        "find_new_plants.py"
    )

    # --------------------------------------------------------
    # 7. 새 식물 화합물 수집
    # --------------------------------------------------------

    run_script(
        "collect_new_plant_compounds.py"
    )

    # --------------------------------------------------------
    # 8. PubChem 연결
    # --------------------------------------------------------

    run_script(
        "link_new_plant_pubchem.py"
    )

    # --------------------------------------------------------
    # 9. ChEMBL 연결
    # --------------------------------------------------------

    run_script(
        "link_new_plant_chembl.py"
    )

    # --------------------------------------------------------
    # 10. ChEMBL 재시도
    # --------------------------------------------------------

    run_script(
        "retry_new_plant_chembl.py"
    )

    # --------------------------------------------------------
    # 11. RDKit Feature 생성
    # --------------------------------------------------------

    run_script(
        "make_new_plant_rdkit_features.py"
    )

    # --------------------------------------------------------
    # 12. AI 입력 데이터 생성
    # --------------------------------------------------------

    run_script(
        "prepare_new_plant_ai_prediction.py"
    )

    # --------------------------------------------------------
    # 13. AI 예측
    # --------------------------------------------------------

    run_script(
        "predict_new_plant_targets.py"
    )

    # --------------------------------------------------------
    # 14. 기존 AI 데이터에 자동 통합
    # --------------------------------------------------------

    run_script(
        "merge_new_plant_ai_predictions.py"
    )

    # --------------------------------------------------------
    # 15. T2D AI 예측
    # --------------------------------------------------------

    run_script(
        "make_t2d_predictions.py"
    )

    # --------------------------------------------------------
    # 16. T2D 우선순위 점수 계산
    # --------------------------------------------------------

    run_script(
        "score_t2d_plants.py"
    )

    # --------------------------------------------------------
    # 17. T2D 상세 분석
    # --------------------------------------------------------

    run_script(
        "analyze_t2d_plant.py"
    )

    # --------------------------------------------------------
    # 18. T2D 웹 데이터 생성
    # --------------------------------------------------------

    run_script(
        "make_t2d_web_data.py"
    )

    # --------------------------------------------------------
    # 19. 약용식물 분포 데이터 수집
    # --------------------------------------------------------

    run_script(
        "collect_new_plant_distribution.py"
    )

    # --------------------------------------------------------
    # 20. 완료
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print("새 약용식물 자동 분석 완료")
    print("=" * 70)

    print()
    print("Plant_ID :", plant_id)
    print("한국어   :", common_name_ko)
    print("영어     :", english_name)
    print("학명     :", scientific_name)

    print()
    print("AI 결과 파일:")
    print(
        "data/processed/new_plant_ai_predictions.csv"
    )

    print()
    print("다음 단계에서 이 결과를 기존 GeoPharm")
    print("AI 데이터와 웹사이트에 연결합니다.")

    print()

    return plant_id

if __name__ == "__main__":
    main()