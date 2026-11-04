import os
import shutil
import pandas as pd


BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)


MAIN_FILE = os.path.join(
    BASE_DIR,
    "data",
    "processed",
    "plant_ai_predictions.csv"
)


NEW_FILE = os.path.join(
    BASE_DIR,
    "data",
    "processed",
    "new_plant_ai_predictions.csv"
)


BACKUP_FILE = os.path.join(
    BASE_DIR,
    "data",
    "processed",
    "plant_ai_predictions_backup_before_merge.csv"
)


# ============================================================
# 새 AI 예측 결과를 기존 AI 데이터에 통합
# ============================================================

def main():

    print("=" * 70)
    print("GeoPharm - 새 식물 AI 예측 결과 통합")
    print("=" * 70)


    # --------------------------------------------------------
    # 1. 파일 확인
    # --------------------------------------------------------

    if not os.path.exists(MAIN_FILE):

        print()
        print("ERROR: 기존 AI 데이터 파일이 없습니다.")
        print(MAIN_FILE)
        return 1


    if not os.path.exists(NEW_FILE):

        print()
        print("ERROR: 새 식물 AI 데이터 파일이 없습니다.")
        print(NEW_FILE)
        return 1


    # --------------------------------------------------------
    # 2. 기존 AI 데이터 읽기
    # --------------------------------------------------------

    main_df = pd.read_csv(
        MAIN_FILE,
        encoding="utf-8-sig",
        low_memory=False
    )


    # --------------------------------------------------------
    # 3. 새 식물 AI 데이터 읽기
    # --------------------------------------------------------

    new_df = pd.read_csv(
        NEW_FILE,
        encoding="utf-8-sig",
        low_memory=False
    )


    print()
    print("기존 AI 데이터")
    print(
        "행 수:",
        len(main_df)
    )

    print(
        "식물 수:",
        main_df["Plant_ID"].nunique()
    )


    print()
    print("새 AI 데이터")
    print(
        "행 수:",
        len(new_df)
    )

    print(
        "식물 수:",
        new_df["Plant_ID"].nunique()
    )


    # --------------------------------------------------------
    # 4. 필요한 컬럼 확인
    # --------------------------------------------------------

    required_columns = [

        "Plant_ID",

        "Scientific_Name",

        "KNApSAcK_ID",

        "Compound_Name",

        "ChEMBL_ID",

        "UniProt_ID",

        "Predicted_pChEMBL",

        "Common_Name_KO"

    ]


    missing_main = [
        column
        for column in required_columns
        if column not in main_df.columns
    ]


    missing_new = [
        column
        for column in required_columns
        if column not in new_df.columns
    ]


    if missing_main:

        print()
        print("ERROR: 기존 AI 데이터에 필요한 컬럼이 없습니다.")

        for column in missing_main:
            print(" -", column)

        return 1


    if missing_new:

        print()
        print("ERROR: 새 AI 데이터에 필요한 컬럼이 없습니다.")

        for column in missing_new:
            print(" -", column)

        return 1


    # --------------------------------------------------------
    # 5. 컬럼 순서 통일
    # --------------------------------------------------------

    main_df = main_df[
        required_columns
    ].copy()


    new_df = new_df[
        required_columns
    ].copy()


    # --------------------------------------------------------
    # 6. 새 식물 확인
    # --------------------------------------------------------

    # 실제 AI 데이터 행이 존재하는 Plant_ID만 기존 분석 식물로 인정
    plant_row_counts = main_df.groupby("Plant_ID").size()

    existing_plant_ids = set(
        plant_row_counts[plant_row_counts > 0].index
        .astype(str)
        .str.strip()
    )


    new_plant_ids = set(
        new_df["Plant_ID"]
        .astype(str)
        .str.strip()
    )


    already_exists = (
        existing_plant_ids
        & new_plant_ids
    )


    only_new = (
        new_plant_ids
        - existing_plant_ids
    )


    print()
    print("새 식물 확인")

    print(
        "새 AI 파일의 식물:",
        sorted(new_plant_ids)
    )

    print(
        "이미 등록된 식물:",
        sorted(already_exists)
    )

    print(
        "새롭게 추가할 식물:",
        sorted(only_new)
    )


    # --------------------------------------------------------
    # 7. 이미 존재하는 식물은 중복 추가하지 않음
    # --------------------------------------------------------

    new_df = new_df[
        new_df["Plant_ID"].astype(str).str.strip().isin(
            only_new
        )
    ].copy()


    if new_df.empty:

        print()
        print("=" * 70)
        print("추가할 새로운 AI 데이터가 없습니다.")
        print("=" * 70)

        return 0


    # --------------------------------------------------------
    # 8. 기존 AI 데이터 백업
    # --------------------------------------------------------

    shutil.copy2(
        MAIN_FILE,
        BACKUP_FILE
    )


    print()
    print("기존 AI 데이터 백업 완료:")
    print(BACKUP_FILE)


    # --------------------------------------------------------
    # 9. 기존 + 새 AI 데이터 통합
    # --------------------------------------------------------

    merged_df = pd.concat(
        [
            main_df,
            new_df
        ],
        ignore_index=True
    )


    # --------------------------------------------------------
    # 10. 완전 동일한 중복 행 제거
    # --------------------------------------------------------

    before_duplicates = len(
        merged_df
    )


    merged_df = merged_df.drop_duplicates(
        subset=[
            "Plant_ID",
            "ChEMBL_ID",
            "UniProt_ID"
        ]
    ).reset_index(
        drop=True
    )


    removed_duplicates = (
        before_duplicates
        - len(merged_df)
    )


    # --------------------------------------------------------
    # 11. 최종 저장
    # --------------------------------------------------------

    merged_df.to_csv(
        MAIN_FILE,
        index=False,
        encoding="utf-8-sig"
    )


    # --------------------------------------------------------
    # 12. 결과 확인
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print("AI 데이터 통합 완료")
    print("=" * 70)


    print()
    print(
        "추가된 AI 행:",
        len(new_df)
    )


    print(
        "제거된 중복 행:",
        removed_duplicates
    )


    print(
        "최종 AI 행:",
        len(merged_df)
    )


    print(
        "최종 식물 수:",
        merged_df["Plant_ID"].nunique()
    )


    print()
    print("최종 AI 데이터:")
    print(MAIN_FILE)


    print()
    print("추가된 식물:")

    for plant_id in sorted(only_new):

        plant_rows = merged_df[
            merged_df["Plant_ID"].astype(str)
            == plant_id
        ]

        print(
            plant_id,
            "-",
            len(plant_rows),
            "AI 예측"
        )


    print()
    print("=" * 70)
    print("완료")
    print("=" * 70)


    return 0


if __name__ == "__main__":

    raise SystemExit(
        main()
    )