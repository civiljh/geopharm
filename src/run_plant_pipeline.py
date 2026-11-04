import subprocess
import sys
from pathlib import Path
import time


# ============================================================
# GeoPharm 식물 데이터 자동 처리 프로그램
# ============================================================
#
# 역할:
# 1. KNApSAcK 식물-화합물 수집
# 2. PubChem 연결
# 3. ChEMBL 연결
# 4. 식물- AI 연결 분석
# 5. RDKit feature 생성
# 6. Protein feature 생성
# 7. AI 예측 준비
# 8. AI 예측
# 9. AI 예측 결과 분석
# 10. 최종 검증
#
# 기존 프로그램은 수정하지 않고
# 각각의 프로그램을 순서대로 실행한다.
# ============================================================


PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"


STAGES = [
    (
        "1단계: KNApSAcK 식물-화합물 수집",
        "collect_knapsack_plants.py",
    ),
    (
        "2단계: PubChem 연결",
        "link_knapsack_pubchem.py",
    ),
    (
        "3단계: ChEMBL 연결",
        "link_chembl.py",
    ),
    (
        "4단계: 식물-AI 연결",
        "analyze_plant_ai_connection.py",
    ),
    (
        "5단계: RDKit feature 생성",
        "make_rdkit_features.py",
    ),
    (
        "6단계: Protein feature 생성",
        "make_protein_features.py",
    ),
    (
        "7단계: AI 예측 준비",
        "prepare_plant_ai_prediction.py",
    ),
    (
        "8단계: AI 예측 실행",
        "predict_plant_targets.py",
    ),
    (
        "9단계: AI 예측 결과 분석",
        "analyze_plant_ai_predictions.py",
    ),
    (
        "10단계: 최종 식물 데이터 검증",
        "plant_validator.py",
    ),
]


def run_stage(stage_number, stage_name, script_name):

    print()
    print("=" * 70)
    print(f"[{stage_number}/{len(STAGES)}] {stage_name}")
    print("=" * 70)
    print(f"실행 파일: {script_name}")
    print()

    script_path = SRC_DIR / script_name

    if not script_path.exists():

        print()
        print("ERROR: 실행 파일을 찾을 수 없습니다.")
        print(f"파일: {script_path}")
        return False

    start_time = time.time()

    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=str(PROJECT_ROOT),
    )

    elapsed = time.time() - start_time

    print()
    print("-" * 70)
    print(f"{stage_name} 종료")
    print(f"실행 시간: {elapsed:.1f}초")
    print(f"종료 코드: {result.returncode}")
    print("-" * 70)

    if result.returncode != 0:

        print()
        print("!!! 자동화가 중단되었습니다.")
        print()
        print(f"문제가 발생한 단계: {stage_name}")
        print(f"실행 파일: {script_name}")
        print(f"종료 코드: {result.returncode}")
        print()

        return False

    print()
    print(f"✓ {stage_name} 완료")

    return True


def check_required_files():

    required_files = [
        "data/raw/medicinal_plants.csv",
        "data/processed/ml_affinity.csv",
        "data/processed/ml_uniprot_sequences.csv",
        "data/processed/random_forest_ic50_protein.joblib",
    ]

    print()
    print("=" * 70)
    print("자동화 시작 전 기본 파일 확인")
    print("=" * 70)

    missing = []

    for relative_path in required_files:

        path = PROJECT_ROOT / relative_path

        if path.exists():

            print(f"[OK] {relative_path}")

        else:

            print(f"[없음] {relative_path}")
            missing.append(relative_path)

    if missing:

        print()
        print("필수 파일이 없습니다.")
        print()

        for path in missing:
            print(" -", path)

        return False

    print()
    print("기본 파일 확인 완료")

    return True


def main():

    print()
    print("=" * 70)
    print("GeoPharm 식물 데이터 자동 처리 시작")
    print("=" * 70)

    print()
    print("프로젝트 위치:")
    print(PROJECT_ROOT)

    print()
    print("총 자동 처리 단계:", len(STAGES))

    # --------------------------------------------------------
    # 기본 파일 확인
    # --------------------------------------------------------

    if not check_required_files():

        print()
        print("자동 처리를 시작하지 않습니다.")
        return 1

    # --------------------------------------------------------
    # 각 단계 실행
    # --------------------------------------------------------

    total_start = time.time()

    for index, (stage_name, script_name) in enumerate(
        STAGES,
        start=1
    ):

        success = run_stage(
            index,
            stage_name,
            script_name,
        )

        if not success:

            print()
            print("=" * 70)
            print("GeoPharm 자동 처리 실패")
            print("=" * 70)

            return 1

    total_elapsed = time.time() - total_start

    # --------------------------------------------------------
    # 최종 완료
    # --------------------------------------------------------

    print()
    print()
    print("=" * 70)
    print("GeoPharm 식물 데이터 자동 처리 완료")
    print("=" * 70)

    print()
    print(f"전체 실행 시간: {total_elapsed / 60:.1f}분")

    print()
    print("처리 순서:")
    print()

    for index, (stage_name, script_name) in enumerate(
        STAGES,
        start=1
    ):

        print(
            f"{index:2d}. {stage_name}"
            f"  ->  {script_name}"
        )

    print()
    print("주요 결과 파일:")
    print()

    output_files = [
        "data/raw/plant_compounds.csv",
        "data/raw/plant_compounds_pubchem.csv",
        "data/processed/plant_compounds_chembl.csv",
        "data/processed/plant_ai_connection.csv",
        "data/processed/rdkit_features.csv",
        "data/processed/protein_features.csv",
        "data/processed/plant_ai_prediction_ready.csv",
        "data/processed/plant_ai_predictions.csv",
        "data/processed/plant_ai_prediction_summary.csv",
        "data/processed/plant_ai_top_candidates.csv",
        "data/processed/plant_validation_report.csv",
    ]

    for relative_path in output_files:

        path = PROJECT_ROOT / relative_path

        if path.exists():

            print(f"[생성 확인] {relative_path}")

        else:

            print(f"[주의] 결과 파일 없음: {relative_path}")

    print()
    print("=" * 70)
    print("모든 자동 처리 단계가 종료되었습니다.")
    print("=" * 70)

    return 0


if __name__ == "__main__":

    sys.exit(main())