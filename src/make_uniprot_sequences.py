import pandas as pd
import requests
import time


INPUT_FILE = "data/processed/ml_uniprot_details.csv"
OUTPUT_FILE = "data/processed/ml_uniprot_sequences.csv"


# --------------------------------------------------
# 1. ML용 UniProt 데이터 불러오기
# --------------------------------------------------

df = pd.read_csv(INPUT_FILE)

print("UniProt 대상:", len(df))


# --------------------------------------------------
# 2. UniProt 서열 수집
# --------------------------------------------------

session = requests.Session()

sequences = []

for number, uniprot_id in enumerate(df["UniProt_ID"], start=1):

    print(f"[{number}/{len(df)}] {uniprot_id}")

    url = f"https://rest.uniprot.org/uniprotkb/{uniprot_id}.fasta"

    try:
        response = session.get(
            url,
            timeout=30
        )

        if response.status_code == 200:

            lines = response.text.strip().splitlines()

            if len(lines) >= 2:

                sequence = "".join(lines[1:])

                sequences.append({
                    "UniProt_ID": uniprot_id,
                    "Sequence": sequence,
                    "Sequence_Length": len(sequence),
                    "Sequence_Status": "OK"
                })

                print(
                    f"  -> 성공 | 길이: {len(sequence)}"
                )

            else:

                sequences.append({
                    "UniProt_ID": uniprot_id,
                    "Sequence": None,
                    "Sequence_Length": None,
                    "Sequence_Status": "NO_SEQUENCE"
                })

                print("  -> 서열 없음")

        else:

            sequences.append({
                "UniProt_ID": uniprot_id,
                "Sequence": None,
                "Sequence_Length": None,
                "Sequence_Status": f"HTTP_{response.status_code}"
            })

            print(
                f"  -> 실패 | HTTP {response.status_code}"
            )

    except Exception as e:

        sequences.append({
            "UniProt_ID": uniprot_id,
            "Sequence": None,
            "Sequence_Length": None,
            "Sequence_Status": "ERROR"
        })

        print("  -> 오류:", e)

    time.sleep(0.2)


# --------------------------------------------------
# 3. DataFrame 생성
# --------------------------------------------------

sequence_df = pd.DataFrame(sequences)


# --------------------------------------------------
# 4. 기존 UniProt 정보와 결합
# --------------------------------------------------

result = df.merge(
    sequence_df,
    on="UniProt_ID",
    how="left",
    validate="one_to_one"
)


# --------------------------------------------------
# 5. 결과 확인
# --------------------------------------------------

print()
print("===== 서열 수집 결과 =====")
print("전체:", len(result))
print(
    "성공:",
    (result["Sequence_Status"] == "OK").sum()
)
print(
    "실패:",
    (result["Sequence_Status"] != "OK").sum()
)


# --------------------------------------------------
# 6. 저장
# --------------------------------------------------

result.to_csv(
    OUTPUT_FILE,
    index=False,
    encoding="utf-8-sig"
)

print()
print("UniProt 서열 데이터 생성 완료")
print("저장:", OUTPUT_FILE)