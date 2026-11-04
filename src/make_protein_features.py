import pandas as pd


INPUT_FILE = "data/processed/ml_uniprot_sequences.csv"
OUTPUT_FILE = "data/processed/protein_features.csv"


# --------------------------------------------------
# 1. 데이터 불러오기
# --------------------------------------------------

df = pd.read_csv(INPUT_FILE)

print("단백질 데이터:", len(df))


# --------------------------------------------------
# 2. 아미노산 정의
# --------------------------------------------------

amino_acids = list("ACDEFGHIKLMNPQRSTVWY")

hydrophobic = set("AILMFWVY")
aromatic = set("FWY")
positive = set("KR")
negative = set("DE")
polar = set("STNQ")


# --------------------------------------------------
# 3. 단백질별 feature 계산
# --------------------------------------------------

feature_rows = []


for _, row in df.iterrows():

    uniprot_id = row["UniProt_ID"]
    sequence = str(row["Sequence"]).upper()

    length = len(sequence)

    features = {
        "UniProt_ID": uniprot_id,
        "Sequence_Length": length
    }

    # --------------------------------------------------
    # 아미노산별 출현 비율
    # --------------------------------------------------

    for aa in amino_acids:

        count = sequence.count(aa)

        if length > 0:
            fraction = count / length
        else:
            fraction = 0.0

        features[f"AA_{aa}"] = fraction


    # --------------------------------------------------
    # 그룹별 아미노산 비율
    # --------------------------------------------------

    if length > 0:

        features["Hydrophobic_Fraction"] = (
            sum(sequence.count(aa) for aa in hydrophobic)
            / length
        )

        features["Aromatic_Fraction"] = (
            sum(sequence.count(aa) for aa in aromatic)
            / length
        )

        features["Positive_Fraction"] = (
            sum(sequence.count(aa) for aa in positive)
            / length
        )

        features["Negative_Fraction"] = (
            sum(sequence.count(aa) for aa in negative)
            / length
        )

        features["Polar_Fraction"] = (
            sum(sequence.count(aa) for aa in polar)
            / length
        )

    else:

        features["Hydrophobic_Fraction"] = 0.0
        features["Aromatic_Fraction"] = 0.0
        features["Positive_Fraction"] = 0.0
        features["Negative_Fraction"] = 0.0
        features["Polar_Fraction"] = 0.0


    feature_rows.append(features)


# --------------------------------------------------
# 4. DataFrame 생성
# --------------------------------------------------

features = pd.DataFrame(feature_rows)


# --------------------------------------------------
# 5. 결과 확인
# --------------------------------------------------

print()
print("===== Protein Feature =====")
print("단백질:", len(features))
print("Feature 수:", len(features.columns))

print()
print(features.head().to_string(index=False))


# --------------------------------------------------
# 6. 저장
# --------------------------------------------------

features.to_csv(
    OUTPUT_FILE,
    index=False,
    encoding="utf-8-sig"
)

print()
print("Protein feature 생성 완료")
print("저장:", OUTPUT_FILE)