import os
import sys
import subprocess
import pandas as pd


# ============================================================
# GeoPharm
# 새 약용식물 등록 + 분포 데이터 자동 수집
# ============================================================

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


DISTRIBUTION_SCRIPT = os.path.join(
    BASE_DIR,
    "src",
    "collect_new_plant_distribution.py"
)


# ============================================================
# 식물 등록
# ============================================================

def add_plant(
    common_name_ko,
    english_name,
    scientific_name
):

    if not os.path.exists(
        PLANT_FILE
    ):

        print(
            "식물 목록 파일을 찾을 수 없습니다."
        )

        print(
            PLANT_FILE
        )

        return None

    try:

        df = pd.read_csv(
            PLANT_FILE,
            encoding="utf-8-sig"
        )

    except Exception:

        df = pd.read_csv(
            PLANT_FILE,
            encoding="utf-8"
        )

    # --------------------------------------------------------
    # 필수 컬럼 확인
    # --------------------------------------------------------

    required_columns = [
        "Plant_ID",
        "Common_Name_KO",
        "English_Name",
        "Scientific_Name"
    ]

    for column in required_columns:

        if column not in df.columns:

            print(
                f"필수 컬럼이 없습니다: {column}"
            )

            return None

    # --------------------------------------------------------
    # 입력값 정리
    # --------------------------------------------------------

    common_name_ko = str(
        common_name_ko
    ).strip()

    english_name = str(
        english_name
    ).strip()

    scientific_name = str(
        scientific_name
    ).strip()

    if not common_name_ko:

        print(
            "한국명이 비어 있습니다."
        )

        return None

    if not scientific_name:

        print(
            "학명이 비어 있습니다."
        )

        return None

    # --------------------------------------------------------
    # 중복 검사
    # --------------------------------------------------------

    scientific_values = (
        df["Scientific_Name"]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.lower()
    )

    if (
        scientific_values
        == scientific_name.lower()
    ).any():

        existing = df.loc[
            scientific_values
            == scientific_name.lower()
        ].iloc[0]

        print()
        print(
            "이미 등록된 식물입니다."
        )

        print(
            f"Plant_ID: "
            f"{existing['Plant_ID']}"
        )

        print(
            f"한국명: "
            f"{existing['Common_Name_KO']}"
        )

        print(
            f"학명: "
            f"{existing['Scientific_Name']}"
        )

        return None

    # --------------------------------------------------------
    # 한국명 중복 검사
    # --------------------------------------------------------

    korean_values = (
        df["Common_Name_KO"]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.lower()
    )

    if (
        korean_values
        == common_name_ko.lower()
    ).any():

        existing = df.loc[
            korean_values
            == common_name_ko.lower()
        ].iloc[0]

        print()
        print(
            "이미 같은 한국명의 식물이 등록되어 있습니다."
        )

        print(
            f"Plant_ID: "
            f"{existing['Plant_ID']}"
        )

        print(
            f"한국명: "
            f"{existing['Common_Name_KO']}"
        )

        print(
            f"학명: "
            f"{existing['Scientific_Name']}"
        )

        return None

    # --------------------------------------------------------
    # 다음 Plant_ID 생성
    # --------------------------------------------------------

    plant_numbers = []

    for value in df["Plant_ID"]:

        text = str(
            value
        ).strip()

        if text.startswith(
            "PLANT"
        ):

            number_text = text[
                len("PLANT"):
            ]

            try:

                plant_numbers.append(
                    int(number_text)
                )

            except ValueError:

                pass

    if plant_numbers:

        next_number = (
            max(plant_numbers)
            + 1
        )

    else:

        next_number = 1

    plant_id = (
        f"PLANT{next_number:03d}"
    )

    # --------------------------------------------------------
    # 새 식물 추가
    # --------------------------------------------------------

    new_row = {

        "Plant_ID":
            plant_id,

        "Common_Name_KO":
            common_name_ko,

        "English_Name":
            english_name,

        "Scientific_Name":
            scientific_name
    }

    df = pd.concat(
        [
            df,
            pd.DataFrame(
                [new_row]
            )
        ],
        ignore_index=True
    )

    # --------------------------------------------------------
    # 저장
    # --------------------------------------------------------

    df.to_csv(
        PLANT_FILE,
        index=False,
        encoding="utf-8-sig"
    )

    print()
    print("=" * 60)
    print(
        "새 약용식물 등록 완료"
    )
    print("=" * 60)

    print(
        f"Plant_ID: {plant_id}"
    )

    print(
        f"한국명: {common_name_ko}"
    )

    print(
        f"영문명: {english_name}"
    )

    print(
        f"학명: {scientific_name}"
    )

    return plant_id


# ============================================================
# 분포 자동 수집 실행
# ============================================================

def collect_distribution(
    plant_id
):

    if not os.path.exists(
        DISTRIBUTION_SCRIPT
    ):

        print()
        print(
            "분포 수집 프로그램을 찾을 수 없습니다."
        )

        print(
            DISTRIBUTION_SCRIPT
        )

        return False

    print()
    print("=" * 60)
    print(
        f"{plant_id} 분포 데이터 자동 수집 시작"
    )
    print("=" * 60)

    print()
    print(
        "GBIF + iNaturalist를 검색합니다."
    )

    # --------------------------------------------------------
    # 현재 가상환경의 Python 사용
    # --------------------------------------------------------

    python_executable = sys.executable

    # --------------------------------------------------------
    # 분포 수집 프로그램 실행
    #
    # 현재 collect_new_plant_distribution.py는
    # 새 식물을 자동으로 찾아 처리하므로
    # 별도의 Plant_ID 인자를 전달하지 않는다.
    # --------------------------------------------------------

    try:

        result = subprocess.run(

            [
                python_executable,
                DISTRIBUTION_SCRIPT
            ],

            cwd=BASE_DIR,

            check=False
        )

    except Exception as e:

        print()
        print(
            "분포 수집 프로그램 실행 오류:"
        )

        print(e)

        return False

    if result.returncode != 0:

        print()
        print(
            "분포 수집 프로그램이 오류로 종료되었습니다."
        )

        print(
            f"종료 코드: "
            f"{result.returncode}"
        )

        return False

    print()
    print(
        "분포 데이터 자동 수집이 완료되었습니다."
    )

    return True


# ============================================================
# 실행
# ============================================================

def main():

    print("=" * 60)
    print(
        "GeoPharm - 새 약용식물 등록 시스템"
    )
    print("=" * 60)

    print()
    print(
        "새 식물 정보를 입력합니다."
    )

    print()

    common_name_ko = input(
        "한국명: "
    ).strip()

    english_name = input(
        "영문명: "
    ).strip()

    scientific_name = input(
        "학명: "
    ).strip()

    # --------------------------------------------------------
    # 식물 등록
    # --------------------------------------------------------

    plant_id = add_plant(

        common_name_ko,

        english_name,

        scientific_name

    )

    if plant_id is None:

        print()
        print(
            "식물 등록을 중단합니다."
        )

        return

    # --------------------------------------------------------
    # 등록 직후 분포 수집
    # --------------------------------------------------------

    collect_distribution(
        plant_id
    )

    print()
    print("=" * 60)
    print(
        "새 식물 등록 작업 완료"
    )
    print("=" * 60)

    print()
    print(
        "다음 단계:"
    )

    print(
        "웹사이트에서 새 식물을 검색할 수 있도록 "
        "Flask 서버를 재시작해야 합니다."
    )


if __name__ == "__main__":

    main()