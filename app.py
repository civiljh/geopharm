from flask import Flask, request, render_template_string, jsonify, send_file
import pandas as pd
import os
import subprocess


app = Flask(__name__)

# Expensive plant discovery runs multiple scripts and writes to the data files.
# Keep it opt-in so an anonymous public visitor cannot start that pipeline.
ENABLE_PLANT_PIPELINE = os.environ.get(
    "GEOPHARM_ENABLE_PLANT_PIPELINE", "true"
).strip().lower() in {"1", "true", "yes", "on"}


# ============================================================
# 기본 경로
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)


# ============================================================
# 데이터 파일
# ============================================================

PLANT_FILE = os.path.join(
    BASE_DIR,
    "data",
    "raw",
    "medicinal_plants.csv"
)


DISTRIBUTION_FILE = os.path.join(
    BASE_DIR,
    "data",
    "processed",
    "plant_distribution.csv"
)


# T2D Plant 우선Rank 점수
# score_t2d_plants.py에서 생성한 최신 파일을 사용합니다.
T2D_PLANT_FILE = os.path.join(
    BASE_DIR,
    "data",
    "processed",
    "t2d_plant_priority_score.csv"
)

# 이전 웹용 파일은 우선Rank 점수 파일이 없을 때만 예비로 사용합니다.
T2D_PLANT_FALLBACK_FILE = os.path.join(
    BASE_DIR,
    "data",
    "processed",
    "t2d_web_plants.csv"
)


T2D_TARGET_FILE = os.path.join(
    BASE_DIR,
    "data",
    "processed",
    "t2d_web_targets.csv"
)


T2D_TARGET_LIST_FILE = os.path.join(
    BASE_DIR,
    "data",
    "processed",
    "t2d_target_list.csv"
)


T2D_CANDIDATE_FILE = os.path.join(
    BASE_DIR,
    "data",
    "processed",
    "t2d_web_candidates.csv"
)


# 전체 AI 예측 데이터
T2D_FULL_PREDICTION_FILE = os.path.join(
    BASE_DIR,
    "data",
    "processed",
    "t2d_plant_specific_predictions.csv"
)
T2D_ALL_PREDICTION_FILE = os.path.join(
    BASE_DIR,
    "data",
    "processed",
    "t2d_plant_predictions.csv"
)


def load_all_t2d_predictions():

    if not os.path.exists(
        T2D_ALL_PREDICTION_FILE
    ):

        return pd.DataFrame()


    try:

        return pd.read_csv(
            T2D_ALL_PREDICTION_FILE,
            encoding="utf-8-sig"
        )

    except Exception:

        return pd.read_csv(
            T2D_ALL_PREDICTION_FILE,
            encoding="utf-8"
        )


T2D_ALL_PREDICTIONS = load_all_t2d_predictions()

LOGO_FILE = os.path.join(
    BASE_DIR,
    "geopharm_logo.png"
)


# ============================================================
# Plant 데이터
# ============================================================

def load_data():

    if not os.path.exists(
        PLANT_FILE
    ):
        return pd.DataFrame()


    try:

        return pd.read_csv(
            PLANT_FILE,
            encoding="utf-8-sig"
        )

    except Exception:

        return pd.read_csv(
            PLANT_FILE,
            encoding="utf-8"
        )


# ============================================================
# 분포 데이터
# ============================================================

def load_distribution():

    if not os.path.exists(
        DISTRIBUTION_FILE
    ):
        return pd.DataFrame()


    try:

        return pd.read_csv(
            DISTRIBUTION_FILE,
            encoding="utf-8-sig"
        )

    except Exception:

        return pd.read_csv(
            DISTRIBUTION_FILE,
            encoding="utf-8"
        )


# ============================================================
# Plant 검색
# ============================================================

def find_plant(
    keyword
):

    df = load_data()


    if df.empty:
        return None


    keyword = str(
        keyword
    ).strip().lower()


    if not keyword:
        return None


    search_columns = [
        "Plant_ID",
        "Common_Name_KO",
        "English_Name",
        "Scientific_Name"
    ]


    existing_columns = [
        column
        for column in search_columns
        if column in df.columns
    ]


    # 정확히 일치
    for _, row in df.iterrows():

        for column in existing_columns:

            value = str(
                row.get(
                    column,
                    ""
                )
            ).strip().lower()


            if value == keyword:

                return row.to_dict()


    # 부분 일치
    for _, row in df.iterrows():

        for column in existing_columns:

            value = str(
                row.get(
                    column,
                    ""
                )
            ).strip().lower()


            if keyword in value:

                return row.to_dict()


    return None


# ============================================================
# 자동완성용 Plant 목록
# ============================================================

def make_plant_search_list():

    df = load_data()

    if df.empty:
        return []

    def clean_name(value):
        if value is None:
            return ""
        value = str(value).strip()
        if value.lower() in ("", "nan", "none", "null"):
            return ""
        return value

    results = []

    for _, row in df.iterrows():
        ko = clean_name(row.get("Common_Name_KO", ""))
        english = clean_name(row.get("English_Name", ""))
        scientific = clean_name(row.get("Scientific_Name", ""))

        results.append({
            "plant_id": clean_name(row.get("Plant_ID", "")),
            "ko": ko,
            "english": english or scientific or ko or "Unknown Plant",
            "scientific": scientific
        })

    return results


PLANT_SEARCH_LIST = make_plant_search_list()


# ============================================================
# 안전한 값 변환
# ============================================================

def safe_value(
    value
):

    if pd.isna(value):
        return None


    if hasattr(
        value,
        "item"
    ):

        try:

            return value.item()

        except Exception:

            pass


    return value


# ============================================================
# T2D 웹 데이터
# ============================================================

def load_t2d_data():

    plants = pd.DataFrame()

    targets = pd.DataFrame()

    candidates = pd.DataFrame()


    # 최신 T2D Plant 우선Rank 점수 파일을 우선 사용합니다.
    plant_source = None

    if os.path.exists(T2D_PLANT_FILE):

        plant_source = T2D_PLANT_FILE

    elif os.path.exists(T2D_PLANT_FALLBACK_FILE):

        plant_source = T2D_PLANT_FALLBACK_FILE


    if plant_source:

        try:

            plants = pd.read_csv(
                plant_source,
                encoding="utf-8-sig"
            )

        except Exception:

            plants = pd.read_csv(
                plant_source,
                encoding="utf-8"
            )


    if os.path.exists(
        T2D_TARGET_FILE
    ):

        try:

            targets = pd.read_csv(
                T2D_TARGET_FILE,
                encoding="utf-8-sig"
            )

        except Exception:

            targets = pd.read_csv(
                T2D_TARGET_FILE,
                encoding="utf-8"
            )


    if os.path.exists(
        T2D_CANDIDATE_FILE
    ):

        try:

            candidates = pd.read_csv(
                T2D_CANDIDATE_FILE,
                encoding="utf-8-sig"
            )

        except Exception:

            candidates = pd.read_csv(
                T2D_CANDIDATE_FILE,
                encoding="utf-8"
            )


    if (
        not plants.empty
        and "Priority_Rank" in plants.columns
    ):

        plants["Priority_Rank"] = pd.to_numeric(
            plants["Priority_Rank"],
            errors="coerce"
        )

        plants = plants.sort_values(
            "Priority_Rank",
            ascending=True,
            na_position="last"
        ).reset_index(drop=True)


    return (
        plants,
        targets,
        candidates
    )

T2D_PLANTS, T2D_TARGETS, T2D_CANDIDATES = load_t2d_data()


# ============================================================
# 질병-Target 연결 데이터
#
# 현재는 제2형 당뇨병의 Related Targets 6개가 들어 있습니다.
# ============================================================

def load_disease_target_list():

    if not os.path.exists(
        T2D_TARGET_LIST_FILE
    ):
        return pd.DataFrame()


    try:

        return pd.read_csv(
            T2D_TARGET_LIST_FILE,
            encoding="utf-8-sig"
        )

    except Exception:

        return pd.read_csv(
            T2D_TARGET_LIST_FILE,
            encoding="utf-8"
        )


DISEASE_TARGET_LIST = load_disease_target_list()


# ============================================================
# 전체 AI 예측 데이터
#
# t2d_plant_specific_predictions.csv
#
# Plant → Compound → Target → AI 예측값
# ============================================================

def load_full_ai_predictions():

    if not os.path.exists(
        T2D_FULL_PREDICTION_FILE
    ):

        return pd.DataFrame()


    try:

        return pd.read_csv(
            T2D_FULL_PREDICTION_FILE,
            encoding="utf-8-sig"
        )

    except Exception:

        return pd.read_csv(
            T2D_FULL_PREDICTION_FILE,
            encoding="utf-8"
        )


T2D_FULL_PREDICTIONS = load_full_ai_predictions()


# ============================================================
# 로고
# ============================================================

@app.route(
    "/geopharm-logo"
)
def geopharm_logo():

    if not os.path.exists(
        LOGO_FILE
    ):
        return "", 404


    return send_file(
        LOGO_FILE
    )


# ============================================================
# Plant 자동완성 API
# ============================================================

@app.route(
    "/api/plant-search"
)
def plant_search():

    keyword = request.args.get(
        "q",
        ""
    ).strip().lower()


    if not keyword:

        return jsonify(PLANT_SEARCH_LIST)


    matches = []


    for plant in PLANT_SEARCH_LIST:

        values = [

            plant.get(
                "ko",
                ""
            ),

            plant.get(
                "english",
                ""
            ),

            plant.get(
                "scientific",
                ""
            ),

            plant.get(
                "plant_id",
                ""
            )

        ]


        matched = False


        for value in values:

            if (
                keyword
                in str(value).lower()
            ):

                matched = True

                break


        if matched:

            matches.append(
                plant
            )


    return jsonify(
        matches[:10]
    )


@app.route("/api/plant-name-resolve")
def plant_name_resolve_api():
    """Find verified plant scientific names for an unregistered English name."""
    if not ENABLE_PLANT_PIPELINE:
        return jsonify({"error": "Plant name lookup is disabled."}), 503

    keyword = request.args.get("q", "").strip()
    if len(keyword) < 3 or len(keyword) > 100:
        return jsonify([])

    try:
        from src.resolve_plant_name import (
            resolve_candidates,
            resolve_inaturalist_candidates,
            search_plant_name,
        )

        candidates = resolve_candidates(search_plant_name(keyword))
        inat_candidates = resolve_inaturalist_candidates(keyword)

        # Prefer an exact common-name match from iNaturalist when available,
        # matching the decision used by the full registration flow.
        if inat_candidates and inat_candidates[0].get("score", 0) >= 100:
            candidates = [inat_candidates[0]]
        elif not candidates:
            candidates = inat_candidates

        unique = {}
        for candidate in candidates:
            scientific_name = candidate.get("scientific_name", "").strip()
            if scientific_name:
                unique.setdefault(scientific_name.lower(), {
                    "english": keyword,
                    "scientific": scientific_name,
                    "external_candidate": True,
                })

        return jsonify(list(unique.values())[:10])
    except Exception:
        app.logger.exception("Plant name lookup failed for %r", keyword)
        return jsonify({"error": "Plant name lookup failed."}), 502


# ============================================================
# 질병 자동완성 검색
# ============================================================

@app.route(
    "/api/disease-search"
)
def disease_search_api():

    keyword = request.args.get(
        "q",
        ""
    ).strip().lower()


    if not keyword:

        return jsonify([])


    disease_names = []

    if not DISEASE_TARGET_LIST.empty and "Disease" in DISEASE_TARGET_LIST.columns:

        disease_names = sorted(
            DISEASE_TARGET_LIST["Disease"]
            .dropna()
            .astype(str)
            .str.strip()
            .unique()
            .tolist()
        )


    aliases = {
        "당뇨병": "Type 2 diabetes mellitus",
        "제2형 당뇨병": "Type 2 diabetes mellitus",
        "제 2형 당뇨병": "Type 2 diabetes mellitus",
        "type 2 diabetes": "Type 2 diabetes mellitus",
        "type 2 diabetes mellitus": "Type 2 diabetes mellitus"
    }


    results = []

    for disease in disease_names:

        disease_lower = disease.lower()

        if keyword in disease_lower:

            results.append({
                "name": disease,
                "display": disease
            })


    for alias, disease in aliases.items():

        if keyword in alias.lower():

            if not any(
                item["name"] == disease
                for item in results
            ):

                results.append({
                    "name": disease,
                    "display": alias
                })


    return jsonify(
        results[:10]
    )


# ============================================================
# Search Disease
# ============================================================

@app.route(
    "/disease",
    methods=["GET"]
)
def disease_search():

    keyword = request.args.get(
        "disease",
        ""
    ).strip()


    disease_name = ""

    target_df = pd.DataFrame()


    if not DISEASE_TARGET_LIST.empty and keyword:

        if "Disease" in DISEASE_TARGET_LIST.columns:

            disease_values = (
                DISEASE_TARGET_LIST["Disease"]
                .dropna()
                .astype(str)
                .str.strip()
            )

            # 현재 데이터의 영문 질병명과
            # 사용자가 입력하기 쉬운 한글 이름을 함께 지원합니다.
            keyword_lower = keyword.lower()

            korean_aliases = {
                "당뇨병": "Type 2 diabetes mellitus",
                "제2형 당뇨병": "Type 2 diabetes mellitus",
                "제 2형 당뇨병": "Type 2 diabetes mellitus",
                "type 2 diabetes": "Type 2 diabetes mellitus",
                "type 2 diabetes mellitus": "Type 2 diabetes mellitus"
            }

            normalized_keyword = korean_aliases.get(
                keyword_lower,
                keyword
            )

            matched = disease_values[
                disease_values.str.lower()
                == normalized_keyword.lower()
            ]

            if matched.empty:

                matched = disease_values[
                    disease_values.str.lower().str.contains(
                        normalized_keyword.lower(),
                        na=False
                    )
                ]


            if not matched.empty:

                disease_name = matched.iloc[0]

                target_df = DISEASE_TARGET_LIST[
                    DISEASE_TARGET_LIST["Disease"].astype(str).str.strip()
                    == disease_name
                ].copy()


    targets = []

    for _, row in target_df.iterrows():

        targets.append({

            "Gene_Name": safe_value(
                row.get("Gene_Name")
            ),

            "UniProt_ID": safe_value(
                row.get("UniProt_ID")
            ),

            "Protein_Name": safe_value(
                row.get("Protein_Name")
            ),

            "Target_Evidence": safe_value(
                row.get("Target_Evidence")
            ),

            "Target_Role": safe_value(
                row.get("Target_Role")
            ),

            "Evidence_Note": safe_value(
                row.get("Evidence_Note")
            )

        })


    candidates = []

    if (
        disease_name
        and not T2D_FULL_PREDICTIONS.empty
        and "UniProt_ID" in T2D_FULL_PREDICTIONS.columns
    ):

        target_ids = set(
            target_df["UniProt_ID"]
            .dropna()
            .astype(str)
        )

        candidate_df = T2D_FULL_PREDICTIONS[
            T2D_FULL_PREDICTIONS["UniProt_ID"].astype(str)
            .isin(target_ids)
        ].copy()

        if not candidate_df.empty:

            candidate_df["Predicted_pChEMBL"] = pd.to_numeric(
                candidate_df["Predicted_pChEMBL"],
                errors="coerce"
            )

            candidate_df = candidate_df.sort_values(
                "Predicted_pChEMBL",
                ascending=False,
                na_position="last"
            )

            plant_df = load_data()

            if not plant_df.empty and "Plant_ID" in plant_df.columns:

                plant_names = plant_df[[
                    "Plant_ID",
                    "Common_Name_KO",
                    "English_Name",
                    "Scientific_Name"
                ]].copy()

                candidate_df = candidate_df.merge(
                    plant_names,
                    on="Plant_ID",
                    how="left"
                )

            seen = set()

            for _, row in candidate_df.iterrows():

                key = (
                    str(row.get("Plant_ID", "")),
                    str(row.get("Compound_Name", "")),
                    str(row.get("UniProt_ID", ""))
                )

                if key in seen:
                    continue

                seen.add(key)

                candidates.append({

                    "Plant_ID": safe_value(row.get("Plant_ID")),
                    "Common_Name_KO": safe_value(row.get("Common_Name_KO")),
                    "English_Name": safe_value(row.get("English_Name")),
                    "Scientific_Name": safe_value(row.get("Scientific_Name")),
                    "Compound_Name": safe_value(row.get("Compound_Name")),
                    "ChEMBL_ID": safe_value(row.get("ChEMBL_ID")),
                    "UniProt_ID": safe_value(row.get("UniProt_ID")),
                    "Protein_Name": safe_value(row.get("Protein_Name")),
                    "Gene_Name": safe_value(row.get("Gene_Name")),
                    "Predicted_pChEMBL": safe_value(row.get("Predicted_pChEMBL"))

                })

                if len(candidates) >= 20:
                    break


    return render_template_string(

        DISEASE_HTML,

        disease_keyword=keyword,
        disease_name=disease_name,
        targets=targets,
        candidates=candidates

    )


# ============================================================
# 주요 AI 후보 10개 API
# ============================================================

@app.route(
    "/api/ai-detail/<plant_id>"
)
def api_ai_detail(
    plant_id
):

    # 최신 전체 T2D 예측 데이터를 사용합니다.
    prediction_df = load_all_t2d_predictions()


    if prediction_df.empty:

        return jsonify({

            "plant_id": plant_id,

            "count": 0,

            "records": []

        })


    if "Plant_ID" not in prediction_df.columns:

        return jsonify({

            "plant_id": plant_id,

            "count": 0,

            "records": []

        })


    plant_df = prediction_df[
        prediction_df["Plant_ID"].astype(str)
        == str(plant_id)
    ].copy()


    if plant_df.empty:

        return jsonify({

            "plant_id": plant_id,

            "count": 0,

            "records": []

        })


    if "Predicted_pChEMBL" in plant_df.columns:

        plant_df["Predicted_pChEMBL"] = pd.to_numeric(
            plant_df["Predicted_pChEMBL"],
            errors="coerce"
        )

        plant_df = plant_df.sort_values(
            "Predicted_pChEMBL",
            ascending=False,
            na_position="last"
        )


    # 주요 AI 후보 10개만 표시합니다.
    plant_df = plant_df.head(10)


    records = []


    wanted_columns = [

        "Plant_ID",

        "Scientific_Name",

        "Common_Name_KO",

        "Compound_Name",

        "ChEMBL_ID",

        "UniProt_ID",

        "Protein_Name",

        "Gene_Name",

        "Predicted_pChEMBL",

        "Target_Evidence",

        "Target_Role",

        "Evidence_Note"

    ]


    for _, row in plant_df.iterrows():

        record = {}


        for column in wanted_columns:

            if column in plant_df.columns:

                record[column] = safe_value(
                    row[column]
                )


        records.append(
            record
        )


    return jsonify({

        "plant_id": str(plant_id),

        "count": len(records),

        "records": records

    })
    # 주요 AI 후보 10개만 표시
    plant_df = plant_df.head(10)


    records = []


    wanted_columns = [

        "Plant_ID",

        "Scientific_Name",

        "KNApSAcK_ID",

        "Compound_Name",

        "ChEMBL_ID",

        "UniProt_ID",

        "Predicted_pChEMBL",

        "Common_Name_KO"

    ]


    for _, row in plant_df.iterrows():

        record = {}


        for column in wanted_columns:

            if column in plant_df.columns:

                record[column] = safe_value(
                    row[column]
                )


        records.append(
            record
        )


    return jsonify({

        "plant_id": str(plant_id),

        "count": len(records),

        "records": records

    })


    if "Predicted_pChEMBL" in plant_df.columns:

        plant_df["Predicted_pChEMBL"] = pd.to_numeric(
            plant_df["Predicted_pChEMBL"],
            errors="coerce"
        )

        plant_df = plant_df.sort_values(
            "Predicted_pChEMBL",
            ascending=False,
            na_position="last"
        )


    records = []


    wanted_columns = [

        "Plant_ID",

        "Scientific_Name",

        "Key_Candidate_Rank",

        "Compound_Name",

        "ChEMBL_ID",

        "UniProt_ID",

        "Predicted_pChEMBL",

        "Target_Evidence",

        "Target_Role",

        "Priority_Rank",

        "Priority_Score",

        "Compound_Compound_Evidence_Level",

        "Reliability_Category",

        "Target_Rank",

        "Target_Priority_Score"

    ]


    for _, row in plant_df.iterrows():

        record = {}


        for column in wanted_columns:

            if column in plant_df.columns:

                record[column] = safe_value(
                    row[column]
                )


        records.append(
            record
        )


    return jsonify({

        "plant_id": str(plant_id),

        "count": len(records),

        "records": records

    })


# ============================================================
# 전체 AI 후보 Compound API
#
# 예:
# 감초 PLANT004
# 47개 Compound × 6개 Target = 282개 예측
# ============================================================

@app.route(
    "/api/ai-full/<plant_id>"
)
def api_ai_full(
    plant_id
):

    # 최신 전체 T2D 예측 데이터를 사용합니다.
    prediction_df = load_all_t2d_predictions()


    if prediction_df.empty:

        return jsonify({

            "plant_id": plant_id,

            "count": 0,

            "compound_count": 0,

            "target_count": 0,

            "records": []

        })


    if "Plant_ID" not in prediction_df.columns:

        return jsonify({

            "plant_id": plant_id,

            "count": 0,

            "compound_count": 0,

            "target_count": 0,

            "records": []

        })


    plant_df = prediction_df[
        prediction_df["Plant_ID"].astype(str)
        == str(plant_id)
    ].copy()


    if plant_df.empty:

        return jsonify({

            "plant_id": plant_id,

            "count": 0,

            "compound_count": 0,

            "target_count": 0,

            "records": []

        })


    if "Predicted_pChEMBL" in plant_df.columns:

        plant_df["Predicted_pChEMBL"] = pd.to_numeric(
            plant_df["Predicted_pChEMBL"],
            errors="coerce"
        )


    sort_columns = []

    ascending_values = []


    if "Compound_Name" in plant_df.columns:

        sort_columns.append(
            "Compound_Name"
        )

        ascending_values.append(
            True
        )


    if "Predicted_pChEMBL" in plant_df.columns:

        sort_columns.append(
            "Predicted_pChEMBL"
        )

        ascending_values.append(
            False
        )


    if sort_columns:

        plant_df = plant_df.sort_values(
            sort_columns,
            ascending=ascending_values,
            na_position="last"
        )


    wanted_columns = [

        "Plant_ID",

        "Scientific_Name",

        "Common_Name_KO",

        "Compound_Name",

        "ChEMBL_ID",

        "UniProt_ID",

        "Protein_Name",

        "Gene_Name",

        "Disease",

        "Predicted_pChEMBL",

        "Target_Evidence",

        "Target_Role",

        "Evidence_Note"

    ]


    records = []


    for _, row in plant_df.iterrows():

        record = {}


        for column in wanted_columns:

            if column in plant_df.columns:

                record[column] = safe_value(
                    row[column]
                )


        records.append(
            record
        )


    compound_count = 0

    target_count = 0


    if "Compound_Name" in plant_df.columns:

        compound_count = int(
            plant_df["Compound_Name"]
            .nunique()
        )


    if "UniProt_ID" in plant_df.columns:

        target_count = int(
            plant_df["UniProt_ID"]
            .nunique()
        )


    return jsonify({

        "plant_id": str(plant_id),

        "count": len(records),

        "compound_count": compound_count,

        "target_count": target_count,

        "records": records

    })

# ============================================================
# 분포 데이터 API
# ============================================================

@app.route(
    "/api/distribution/<plant_id>"
)
def api_distribution(
    plant_id
):

    df = load_distribution()


    if df.empty:

        return jsonify({

            "plant_id": plant_id,

            "count": 0,

            "records": []

        })


    if "Plant_ID" not in df.columns:

        return jsonify({

            "plant_id": plant_id,

            "count": 0,

            "records": []

        })


    plant_df = df[
        df["Plant_ID"].astype(str)
        == str(plant_id)
    ].copy()


    records = []


    for _, row in plant_df.iterrows():

        record = {}


        for column in plant_df.columns:

            record[column] = safe_value(
                row[column]
            )


        records.append(
            record
        )


    return jsonify({

        "plant_id": plant_id,

        "count": len(records),

        "records": records

    })


# ============================================================
# HTML
# ============================================================

DISEASE_HTML = r"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GeoPharm - Search Disease</title>
    <style>
        body {
            margin: 0;
            font-family: Arial, "Malgun Gothic", sans-serif;
            background: #f7f0df;
            color: #31543b;
        }
        .header {
            padding: 24px;
            background: #f7f0df;
            border-bottom: 1px solid #ded4bf;
        }
        .header-inner {
            max-width: 1400px;
            margin: 0 auto;
        }
        .disease-logo {
            display: inline-block;
            color: #31543b;
            font-size: 32px;
            line-height: 1.2;
            font-weight: 700;
        }
        .header a {
            color: #31543b;
            text-decoration: none;
            font-weight: bold;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 24px;
        }
        .search-box, .card {
            background: #fffaf0;
            border: 1px solid #ded4bf;
            border-radius: 16px;
            padding: 18px;
            margin-bottom: 18px;
            box-shadow: 0 4px 15px rgba(70, 80, 50, 0.06);
        }
        .search-form {
            display: flex;
            gap: 10px;
        }
        .search-input-wrap {
            flex: 1;
        }
        input {
            width: 100%;
            box-sizing: border-box;
            padding: 12px 14px;
            border: 1px solid #ded4bf;
            border-radius: 8px;
            font-size: 15px;
        }
        button {
            border: 0;
            border-radius: 8px;
            padding: 12px 18px;
            background: #31543b;
            color: white;
            font-weight: bold;
            cursor: pointer;
        }
        h1, h2 {
            margin-top: 0;
        }
        .muted {
            color: #667866;
            font-size: 13px;
            line-height: 1.6;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 14px;
        }
        th, td {
            padding: 10px;
            border-bottom: 1px solid #e3dccd;
            text-align: left;
            vertical-align: top;
            font-size: 13px;
        }
        th {
            background: #f3eddf;
            color: #4e654f;
        }
        .score {
            font-weight: bold;
        }
        @media (max-width: 700px) {
            .search-form {
                flex-direction: column;
            }
            .container {
                padding: 12px;
            }
        }
    </style>
</head>
<body>
    <header class="header">
        <div class="header-inner">
            <a class="disease-logo" href="/" aria-label="GeoPharm home">GeoPharm</a>
            <div class="muted">Disease → Targets → Candidate Compounds → Candidate Plants</div>
        </div>
    </header>

    <main class="container">
        <div class="search-box">
            <form class="search-form" method="get" action="/disease">
                <div class="search-input-wrap">
                    <input
                        type="text"
                        name="disease"
                        value="{{ disease_keyword }}"
                        placeholder="Enter a disease name (e.g., Type 2 Diabetes)"
                    >
                </div>
                <button type="submit">Search Disease</button>
            </form>
        </div>

        {% if disease_name %}
        <div class="card">
            <h1>{{ disease_name }}</h1>
            <div class="muted">
                Displays disease-related targets and AI-predicted candidates currently available in the database.
            </div>
        </div>

        <div class="card">
            <h2>Related Targets</h2>
            <table>
                <thead>
                    <tr>
                        <th>Target</th>
                        <th>UniProt</th>
                        <th>Evidence</th>
                        <th>Target Role</th>
                    </tr>
                </thead>
                <tbody>
                {% for target in targets %}
                    <tr>
                        <td>{{ target.Gene_Name or "-" }}<br>{{ target.Protein_Name or "-" }}</td>
                        <td>{{ target.UniProt_ID or "-" }}</td>
                        <td>{{ target.Target_Evidence or "-" }}</td>
                        <td>{{ target.Target_Role or "-" }}</td>
                    </tr>
                {% endfor %}
                </tbody>
            </table>
        </div>

        <div class="card">
            <h2>AI-Predicted Candidate Compounds and Plants</h2>
            <div class="muted">
                Candidates with higher AI prediction scores are prioritized. These results do not prove actual binding or therapeutic effects.
            </div>
            {% if candidates %}
            <table>
                <thead>
                    <tr>
                        <th>Plant</th>
                        <th>Compound</th>
                        <th>Target</th>
                        <th>AI-Predicted pChEMBL</th>
                    </tr>
                </thead>
                <tbody>
                {% for candidate in candidates %}
                    <tr>
                        <td>
                            {{ candidate.Common_Name_KO or "-" }}<br>
                            <span class="muted">{{ candidate.Scientific_Name or "-" }}</span>
                        </td>
                        <td>
                            {{ candidate.Compound_Name or "-" }}<br>
                            <span class="muted">{{ candidate.ChEMBL_ID or "-" }}</span>
                        </td>
                        <td>
                            {{ candidate.Gene_Name or "-" }}<br>
                            <span class="muted">{{ candidate.Protein_Name or "-" }}</span>
                        </td>
                        <td class="score">{{ "%.3f"|format(candidate.Predicted_pChEMBL|float) }}</td>
                    </tr>
                {% endfor %}
                </tbody>
            </table>
            {% else %}
            <p class="muted">No linked AI-predicted candidates were found.</p>
            {% endif %}
        </div>
        {% elif disease_keyword %}
        <div class="card">
            <h2>No Search Results</h2>
            <p class="muted">Currently, Type 2 Diabetes is the primary disease connected in the database.</p>
        </div>
        {% endif %}
    </main>
</body>
</html>
"""


HTML = r"""
<!DOCTYPE html>

<html lang="en">

<head>

<meta charset="UTF-8">

<meta
    name="viewport"
    content="width=device-width, initial-scale=1.0"
>

<title>GeoPharm</title>


<!-- Leaflet -->

<link
    rel="stylesheet"
    href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
>


<!-- MarkerCluster -->

<link
    rel="stylesheet"
    href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.css"
>

<link
    rel="stylesheet"
    href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.Default.css"
>


<style>

/* =========================================================
   전체
   ========================================================= */

* {
    box-sizing: border-box;
}


body {

    margin: 0;

    background: #f7f0df;

    color: #31543b;

    font-family:
        Arial,
        "Malgun Gothic",
        sans-serif;
}


/* =========================================================
   헤더
   ========================================================= */

.header {

    width: 100%;

    background: #f7f0df;

    padding:
        25px
        30px
        15px
        30px;

    border-bottom:
        1px solid
        #ded4bf;
}


.header-inner {

    max-width: 1400px;

    margin: auto;
}


.logo {

    color: #31543b;

    font-size: 48px;

    line-height: 1.2;

    font-weight: 700;
}


.subtitle {

    margin-top: 8px;

    color: #667866;

    font-size: 14px;
}


/* =========================================================
   컨테이너
   ========================================================= */

.container {

    max-width: 1400px;

    margin:
        25px
        auto
        50px
        auto;

    padding:
        0
        25px;
}


/* =========================================================
   검색
   ========================================================= */

.search-box {

    position: relative;

    background: #fffaf0;

    border:
        1px solid
        #ded4bf;

    border-radius: 16px;

    padding: 20px;

    box-shadow:
        0 4px 15px
        rgba(
            70,
            80,
            50,
            0.06
        );
}


.search-form {

    display: flex;

    gap: 10px;
}


.search-input-wrap {

    position: relative;

    flex: 1;
}


.search-form input {

    width: 100%;

    min-width: 0;

    padding:
        14px
        16px;

    border:
        1px solid
        #c9c0ab;

    border-radius: 10px;

    background: white;

    font-size: 16px;

    outline: none;
}


.search-form input:focus {

    border-color: #4d7c59;

    box-shadow:
        0 0 0 3px
        rgba(
            77,
            124,
            89,
            0.12
        );
}


.search-form button {

    border: 0;

    border-radius: 10px;

    padding:
        14px
        25px;

    background: #4d7c59;

    color: white;

    font-weight: bold;

    cursor: pointer;
}


.search-form button:hover {

    background: #3e6749;
}


/* =========================================================
   자동완성
   ========================================================= */

.autocomplete {

    position: absolute;

    left: 0;

    right: 0;

    top: calc(100% + 5px);

    z-index: 3000;

    background: white;

    border:
        1px solid
        #d8cfbc;

    border-radius: 10px;

    box-shadow:
        0 8px 25px
        rgba(
            0,
            0,
            0,
            0.12
        );

    max-height: 420px;
    overflow-y: auto;

    display: none;
}


.autocomplete-item {

    padding:
        12px
        15px;

    cursor: pointer;

    border-bottom:
        1px solid
        #eee8da;
}


.autocomplete-item:last-child {

    border-bottom: 0;
}


.autocomplete-item:hover {

    background: #f3f0e6;
}


.autocomplete-ko {

    font-size: 15px;

    font-weight: bold;

    color: #31543b;
}


.autocomplete-sub {

    margin-top: 3px;

    font-size: 12px;

    color: #788071;
}


.autocomplete-empty {

    padding: 13px 15px;

    color: #888;

    font-size: 13px;
}


/* =========================================================
   카드
   ========================================================= */

.card {

    margin-top: 22px;

    background: #fffaf0;

    border:
        1px solid
        #ded4bf;

    border-radius: 16px;

    overflow: hidden;

    box-shadow:
        0 4px 15px
        rgba(
            70,
            80,
            50,
            0.06
        );
}


.card-header {

    padding:
        18px
        22px;

    border-bottom:
        1px solid
        #e4dccb;
}


.card-header h2 {

    margin: 0;

    font-size: 22px;
}


.card-header p {

    margin:
        6px
        0
        0
        0;

    color: #777b6c;

    font-size: 13px;
}


/* =========================================================
   Plant 정보
   ========================================================= */

.info {

    padding:
        18px
        22px;
}


.info-title {

    font-size: 25px;

    font-weight: bold;

    margin-bottom: 5px;
}


.info-scientific {

    color: #687766;

    font-style: italic;
}


/* =========================================================
   AI 결과
   ========================================================= */

.result-grid {

    display: grid;

    grid-template-columns:
        repeat(
            auto-fit,
            minmax(
                230px,
                1fr
            )
        );

    gap: 15px;

    padding: 20px;
}


.result-box {

    background: #f8f4e8;

    border:
        1px solid
        #ded4bf;

    border-radius: 12px;

    padding: 16px;
}


.result-label {

    color: #7a806f;

    font-size: 12px;
}


.result-value {

    margin-top: 5px;

    font-size: 22px;

    font-weight: bold;

    color: #3f6e4d;
}


/* =========================================================
   버튼
   ========================================================= */

.detail-button-wrap {

    padding:
        0
        20px
        20px
        20px;
}


.detail-button-row {

    display: flex;
    align-items: center;
    gap: 14px;
    flex-wrap: wrap;

}


.detail-button-help {

    flex: 1;
    min-width: 280px;
    color: #687366;
    font-size: 13px;
    line-height: 1.6;
}


.detail-button-help span {

    display: block;
    margin-top: 2px;
    color: #8a6f4d;
    font-size: 12px;

}


.detail-button {

    border: 0;

    border-radius: 10px;

    padding:
        12px
        20px;

    background: #4d7c59;

    color: white;

    font-size: 14px;

    font-weight: bold;

    cursor: pointer;
}


.detail-button:hover {

    background: #3e6749;
}


/* =========================================================
   AI 상세 영역
   ========================================================= */

.ai-detail {

    display: none;

    margin:
        0
        20px
        20px
        20px;

    border:
        1px
        solid
        #cbdcc5;

    border-radius: 12px;

    background: #f8fbf5;

    overflow: hidden;
}


.ai-detail-header {

    padding:
        16px
        18px;

    background: #edf3e8;

    border-bottom:
        1px
        solid
        #cbdcc5;
}


.ai-detail-header h3 {

    margin: 0;

    color: #31543b;

    font-size: 18px;
}


.ai-detail-header p {

    margin:
        5px
        0
        0
        0;

    color: #687766;

    font-size: 13px;
}


.ai-detail-status {

    padding:
        14px
        18px;

    color: #687766;

    font-size: 13px;
}


/* =========================================================
   전체 후보 영역
   ========================================================= */

.full-ai-section {

    margin:
        0
        20px
        20px
        20px;

    border:
        1px
        solid
        #cbdcc5;

    border-radius: 12px;

    background: #f8fbf5;

    overflow: hidden;
}


.full-ai-header {

    padding:
        16px
        18px;

    background: #edf3e8;

    border-bottom:
        1px
        solid
        #cbdcc5;
}


.full-ai-header h3 {

    margin: 0;

    font-size: 18px;

    color: #31543b;
}


.full-ai-header p {

    margin:
        6px
        0
        0
        0;

    color: #687766;

    font-size: 13px;

    line-height: 1.5;
}


/* =========================================================
   전체 후보 요약
   ========================================================= */

.full-ai-summary {

    display: grid;

    grid-template-columns:
        repeat(
            3,
            1fr
        );

    gap: 10px;

    padding: 15px;
}


.full-ai-stat {

    background: white;

    border:
        1px
        solid
        #dfe8da;

    border-radius: 9px;

    padding: 12px;

    text-align: center;
}


.full-ai-stat-label {

    font-size: 11px;

    color: #788071;
}


.full-ai-stat-value {

    margin-top: 4px;

    font-size: 20px;

    font-weight: bold;

    color: #3f6e4d;
}


/* =========================================================
   Compound 선택
   ========================================================= */

.compound-selector {

    padding:
        0
        15px
        15px
        15px;
}


.compound-selector label {

    display: block;

    margin-bottom: 7px;

    font-size: 13px;

    font-weight: bold;

    color: #4e654f;
}


.compound-selector select {

    width: 100%;

    padding:
        12px
        13px;

    border:
        1px
        solid
        #cbd5c4;

    border-radius: 9px;

    background: white;

    color: #31543b;

    font-size: 14px;

    outline: none;
}


.compound-selector select:focus {

    border-color: #4d7c59;

    box-shadow:
        0
        0
        0
        3px
        rgba(
            77,
            124,
            89,
            0.10
        );
}


/* =========================================================
   선택된 Compound 정보
   ========================================================= */

.selected-compound {

    margin:
        0
        15px
        15px
        15px;

    padding: 15px;

    border-radius: 10px;

    background: white;

    border:
        1px
        solid
        #dfe8da;
}


.selected-compound-name {

    font-size: 18px;

    font-weight: bold;

    color: #31543b;
}


.selected-compound-id {

    margin-top: 4px;

    color: #788071;

    font-size: 12px;
}


/* =========================================================
   Target 테이블
   ========================================================= */

.target-table-wrap {

    overflow-x: auto;

    padding:
        0
        15px
        15px
        15px;
}


.target-table {

    width: 100%;

    min-width: 900px;

    border-collapse: collapse;

    font-size: 13px;
}


.target-table th,
.target-table td {

    border-bottom:
        1px
        solid
        #dfe8da;

    padding:
        10px
        8px;

    text-align: left;

    vertical-align: top;
}


.target-table th {

    background: #e7efe2;

    color: #4e654f;

    font-weight: bold;
}


.target-table td {

    color: #435347;
}


.target-name {

    font-weight: bold;

    color: #31543b;
}


.target-gene {

    margin-top: 3px;

    color: #788071;

    font-size: 11px;
}


.predicted-score {

    font-size: 15px;

    font-weight: bold;

    color: #3f6e4d;
}


.evidence-badge {

    display: inline-block;

    padding:
        3px
        8px;

    border-radius: 20px;

    background: #e1eee0;

    color: #47654d;

    font-size: 11px;

    font-weight: bold;
}


.role-text {

    line-height: 1.5;
}


.note-text {

    max-width: 420px;

    line-height: 1.5;

    color: #687766;

    font-size: 12px;
}


/* =========================================================
   안내
   ========================================================= */

.ai-detail-note {

    margin:
        0
        15px
        15px
        15px;

    padding:
        12px
        14px;

    border-radius: 8px;

    background: #fffaf0;

    border:
        1px
        solid
        #ded4bf;

    color: #687766;

    font-size: 12px;

    line-height: 1.6;
}


/* =========================================================
   지도
   ========================================================= */

.map-wrap {

    position: relative;

    width: 100%;

    height: 650px;
}


#map {

    width: 100%;

    height: 100%;
}


.map-legend {

    position: absolute;

    right: 15px;

    top: 15px;

    z-index: 1000;

    background:
        rgba(
            255,
            255,
            255,
            0.94
        );

    border-radius: 10px;

    padding:
        12px
        14px;

    box-shadow:
        0 2px 10px
        rgba(
            0,
            0,
            0,
            0.15
        );

    font-size: 13px;

    color: #39483d;
}


.legend-row {

    display: flex;

    align-items: center;

    gap: 7px;

    margin:
        4px
        0;
}


.legend-dot {

    width: 11px;

    height: 11px;

    border-radius: 50%;

    display: inline-block;
}


.legend-inat {

    background: #3388ff;
}


.legend-gbif {

    background: #35a85b;
}


.legend-other {

    background: #777777;
}


.map-footer {

    padding:
        12px
        18px;

    border-top:
        1px
        solid
        #e4dccb;

    color: #687766;

    font-size: 13px;
}


/* =========================================================
   테이블
   ========================================================= */

.t2d-table-wrap {

    overflow-x: auto;

    padding:
        0
        20px
        20px
        20px;
}


table {

    width: 100%;

    border-collapse: collapse;

    font-size: 13px;
}


th,
td {

    border-bottom:
        1px
        solid
        #e3dccd;

    padding:
        10px
        8px;

    text-align: left;
}


th {

    color: #4e654f;

    background: #f3eddf;
}


/* =========================================================
   주의사항
   ========================================================= */

.notice {

    margin-top: 20px;

    padding:
        15px
        18px;

    border-radius: 12px;

    background: #edf3e8;

    border:
        1px
        solid
        #cbdcc5;

    color: #47654d;

    font-size: 13px;

    line-height: 1.6;
}


/* =========================================================
   마커
   ========================================================= */

.marker-dot {

    width: 12px;

    height: 12px;

    border-radius: 50%;

    border:
        2px
        solid
        white;

    box-shadow:
        0 1px 4px
        rgba(
            0,
            0,
            0,
            0.35
        );
}


.marker-inat {

    background: #3388ff;
}


.marker-gbif {

    background: #35a85b;
}


.marker-other {

    background: #777777;
}


/* =========================================================
   푸터
   ========================================================= */

.footer {

    max-width: 1400px;

    margin:
        0
        auto;

    padding: 25px;

    color: #788071;

    font-size: 12px;

    text-align: center;
}


/* =========================================================
   모바일
   ========================================================= */

@media (
    max-width: 700px
) {

    .header {

        padding: 18px;
    }


    .container {

        padding:
            0
            12px;
    }


    .search-form {

        flex-direction: column;
    }


    .map-wrap {

        height: 500px;
    }


    .full-ai-summary {

        grid-template-columns:
            1fr;
    }

}

@keyframes analysisProgress {

    0% {
        width: 15%;
    }

    50% {
        width: 75%;
    }

    100% {
        width: 95%;
    }

}
</style>

</head>


<body>

<!-- =======================================================
     새 Plant 분석 진행 화면
     ======================================================= -->

<div
    id="analysis-loading"
    style="
        display:none;
        position:fixed;
        top:0;
        left:0;
        width:100%;
        height:100%;
        background:rgba(255,255,255,0.92);
        z-index:99999;
        align-items:center;
        justify-content:center;
    "
>

    <div
        style="
            width:min(520px,90%);
            padding:32px;
            background:#ffffff;
            border:1px solid #d7dfd2;
            border-radius:18px;
            box-shadow:0 10px 35px rgba(0,0,0,0.12);
            text-align:center;
        "
    >

        <div
            style="
                font-size:20px;
                font-weight:700;
                color:#315b3b;
                margin-bottom:12px;
            "
        >
            Analyzing medicinal plants...
        </div>

        <div
            style="
                font-size:14px;
                color:#687568;
                margin-bottom:22px;
            "
        >
            Plant Information ? KNApSAcK ? Compound Analysis ?
            AI Predictions ? T2D Analysis ? Distribution Data
        </div>

        <div
            style="
                width:100%;
                height:14px;
                background:#e8eee5;
                border-radius:10px;
                overflow:hidden;
            "
        >

            <div
                id="analysis-progress-bar"
                style="
                    width:35%;
                    height:100%;
                    background:#4e805c;
                    border-radius:10px;
                    animation:analysisProgress 2s ease-in-out infinite;
                "
            ></div>

        </div>

        <div
            id="analysis-progress-text"
            style="
                margin-top:16px;
                font-size:14px;
                color:#4e654f;
            "
        >
            Preparing analysis...
        </div>

        <div
            style="
                margin-top:10px;
                font-size:12px;
                color:#8a9187;
            "
        >
            When the analysis is complete, the results page will open automatically.
        </div>

    </div>

</div>

<!-- =======================================================
     헤더
     ======================================================= -->

<header class="header">

    <div class="header-inner">

        <div class="logo">GeoPharm</div>

        <div class="subtitle">

            Medicinal Plant · Compound · Target ·
            Distribution Analysis

        </div>

    </div>

</header>


<main class="container">


<!-- =======================================================
     검색
     ======================================================= -->

<div class="search-box">

    <form
        class="search-form"
        method="get"
        action="/"
        autocomplete="off"
    >

        <div class="search-input-wrap">

            <input
                id="plant-search"
                type="text"
                name="plant"
                value="{{ keyword }}"
                placeholder="Enter a plant name, English name, or scientific name"
            >


            <div
                id="autocomplete"
                class="autocomplete"
            ></div>

            <input
                id="resolved-scientific-name"
                type="text"
                readonly
                placeholder="Scientific name will appear here"
                aria-label="Resolved scientific name"
                value=""
                style="display:none; margin-top:8px;"
            >

        </div>

        
                {% if name_candidates %}
        <div class="name-candidate-box">

            <div class="name-candidate-title">
                Multiple plants were found. Please select a plant.
            </div>

            {% for candidate in name_candidates %}
            <button
                type="submit"
                name="scientific_name"
                value="{{ candidate.scientific_name }}"
                class="name-candidate-item"
            >
                {{ candidate.scientific_name }}
            </button>
            {% endfor %}

        </div>
        {% endif %}

        
        <button
            type="submit"
            id="plant-analyze-button"
        >
            Analyze
        </button>

    </form>

</div>

{% if keyword and not plant and not name_candidates and not pipeline_enabled %}
<p class="notice">
    This plant is not in the published dataset. New plant analysis is currently unavailable.
</p>
{% endif %}

{% if pipeline_error %}
<p class="notice" role="alert">{{ pipeline_error }}</p>
{% endif %}


<div class="search-box" style="margin-top:16px;">

    <form
        class="search-form"
        method="get"
        action="/disease"
        autocomplete="off"
    >

        <div class="search-input-wrap">

            <input
                id="disease-search"
                type="text"
                name="disease"
                placeholder="Enter a disease name (e.g., Type 2 Diabetes)"
            >

            <div
                id="disease-autocomplete"
                class="autocomplete"
            ></div>

        </div>

        <button type="submit">
            Search Disease
        </button>

    </form>

</div>


{% if plant %}


<!-- =======================================================
     Plant 정보
     ======================================================= -->

<div class="card">

    <div class="info">

        <div class="info-title">

            {{ plant.get("English_Name") or plant.get("Scientific_Name") or plant.get("Common_Name_KO") or keyword }}

        </div>


        <div class="info-scientific">

            {{ plant.get(
                "Scientific_Name",
                ""
            ) }}

        </div>

    </div>

</div>


<!-- =======================================================
     AI 분석
     ======================================================= -->

<div class="card">

    <div class="card-header">

        <h2>
            Diabetes-Related AI Analysis
        </h2>

        <p>
            AI predictions based on medicinal plant compounds and protein targets.
        </p>

    </div>


    <div class="result-grid">


        <div class="result-box">

            <div class="result-label">
                Selected Plant
            </div>


            <div class="result-value">

                {{ plant.get("English_Name") or plant.get("Scientific_Name") or plant.get("Common_Name_KO") or keyword }}

            </div>

        </div>


        <div class="result-box">

            <div class="result-label">
                Scientific Name
            </div>


            <div
                class="result-value"
                style="font-size:17px;"
            >

                {{ plant.get(
                    "Scientific_Name",
                    "-"
                ) }}

            </div>

        </div>


    </div>


    <!-- ===================================================
         T2D Priority Score for the Selected Plant
         =================================================== -->

    {% if selected_t2d_score %}

    <div class="result-grid">

        <div class="result-box">

            <div class="result-label">
                T2D Priority Score
            </div>

            <div class="result-value">

                {% set selected_score =
                    selected_t2d_score.get(
                        "Priority_Score",
                        "-"
                    )
                %}

                {% if selected_score != "-" and selected_score is not none %}

                    {{ "%.3f"|format(
                        selected_score|float
                    ) }}

                {% else %}

                    -

                {% endif %}

            </div>

        </div>


        <div class="result-box">

            <div class="result-label">
                Priority Rank
            </div>

            <div class="result-value">

                {% set selected_rank =
                    selected_t2d_score.get(
                        "Priority_Rank",
                        "-"
                    )
                %}

                {% if selected_rank != "-" and selected_rank is not none %}

                    Rank {{ selected_rank }}

                {% else %}

                    -

                {% endif %}

            </div>

        </div>


        <div class="result-box">

            <div class="result-label">
                Evidence Level · Reliability
            </div>

            <div class="result-value"
                 style="font-size:17px;">

                {{ selected_t2d_score.get(
                    "Compound_Evidence_Level",
                    "-"
                ) }}

                ·

                {{ selected_t2d_score.get(
                    "Reliability_Category",
                    "-"
                ) }}

            </div>

        </div>

    </div>

    <div class="ai-detail-note">

        <strong>About the T2D Priority Score:</strong>
        This internal screening score compares candidate plants for Type 2 Diabetes. A higher score does not mean that therapeutic effects have been confirmed.
    </div>

    {% endif %}


    <!-- ===================================================
         상위 AI 후보 10개
         =================================================== -->

    <div class="t2d-table-wrap">


        {% if not T2D_PLANTS.empty %}


        <table>

            <thead>

                <tr>

                    <th>
                        Rank
                    </th>

                    <th>
                        Plant
                    </th>

                    <th>
                        Compound Count
                    </th>

                    <th>
                        Target Count
                    </th>

                    <th>
                        Maximum Predicted Value
                    </th>

                    <th>
                        Average Predicted Value
                    </th>

                    <th>
                        Priority Score
                    </th>

                    <th>
                        Evidence Level
                    </th>

                    <th>
                        Reliability
                    </th>

                </tr>

            </thead>


            <tbody>


            {% for _, row in
                T2D_PLANTS.head(10).iterrows()
            %}


                <tr>

                    <td>

                        {{ row.get(
                            "Priority_Rank",
                            loop.index
                        ) }}

                    </td>


                    <td>

                        {{ row.get(
                            "Scientific_Name",
                            row.get(
                                "Plant_ID",
                                ""
                            )
                        ) }}

                    </td>


                    <td>

                        {{ row.get(
                            "Compound_Count",
                            "-"
                        ) }}

                    </td>


                    <td>

                        {{ row.get(
                            "Target_Count",
                            "-"
                        ) }}

                    </td>


                    <td>

                        {% set max_value =
                            row.get(
                                "Max_pChEMBL",
                                "-"
                            )
                        %}

                        {% if max_value != "-" %}

                            {{ "%.3f"|format(
                                max_value|float
                            ) }}

                        {% else %}

                            -

                        {% endif %}

                    </td>


                    <td>

                        {% set mean_value =
                            row.get(
                                "Mean_pChEMBL",
                                "-"
                            )
                        %}

                        {% if mean_value != "-" %}

                            {{ "%.3f"|format(
                                mean_value|float
                            ) }}

                        {% else %}

                            -

                        {% endif %}

                    </td>


                    <td>

                        {% set score =
                            row.get(
                                "Priority_Score",
                                "-"
                            )
                        %}

                        {% if score != "-" %}

                            {{ "%.3f"|format(
                                score|float
                            ) }}

                        {% else %}

                            -

                        {% endif %}

                    </td>


                    <td>

                        {{ row.get(
                            "Compound_Evidence_Level",
                            "-"
                        ) }}

                    </td>


                    <td>

                        {{ row.get(
                            "Reliability_Category",
                            "-"
                        ) }}

                    </td>

                </tr>


            {% endfor %}


            </tbody>

        </table>


        {% else %}


        <p>

            T2D analysis data could not be found.

        </p>


        {% endif %}


    </div>


    <!-- ===================================================
         주요 후보 10개 버튼
         =================================================== -->

    <div class="detail-button-wrap">

        <div class="detail-button-row">

            <button
                type="button"
                class="detail-button"
                onclick="loadAIDetail()"
            >
                View Top 10 AI Candidates
            </button>

            <div class="detail-button-help">
                Candidate compounds with higher AI-predicted values are shown first. These predictions do not prove actual binding or therapeutic effects.
                <span>Note: AI predictions do not prove actual binding or therapeutic effects.</span>
            </div>

        </div>

    </div>


    <!-- ===================================================
         주요 후보 10개
         =================================================== -->

    <div
        id="ai-detail"
        class="ai-detail"
    >

        <div class="ai-detail-header">

            <h3>
                Top AI Candidate Compounds
            </h3>

            <p>

                These are the key candidates prioritized for display
                on this page.

            </p>

        </div>


        <div
            id="ai-detail-status"
            class="ai-detail-status"
        >

            Loading AI candidate data...

        </div>


        <div class="target-table-wrap">

            <table class="target-table">

                <thead>

                    <tr>

                        <th>
                            Rank
                        </th>

                        <th>
                            Compound
                        </th>

                        <th>
                            ChEMBL ID
                        </th>

                        <th>
                            UniProt ID
                        </th>

                        <th>
                            AI-Predicted pChEMBL
                        </th>

                        <th>
                            Evidence
                        </th>

                        <th>
                            Target Role
                        </th>

                    </tr>

                </thead>


                <tbody
                    id="ai-detail-body"
                >

                </tbody>

            </table>

        </div>

    </div>


    <!-- ===================================================
All AI Candidates
         =================================================== -->

    <div
        id="full-ai-section"
        class="full-ai-section"
    >

        <div class="full-ai-header">

            <h3>
All AI Candidate Compound Analysis
            </h3>

            <p>

Compounds associated with this plant
AI predictions for six diabetes-related targets per compound
are available below.

            </p>

        </div>


        <!-- 전체 AI 통계 -->

        <div class="full-ai-summary">


            <div class="full-ai-stat">

                <div class="full-ai-stat-label">
AI Prediction Rows
                </div>

                <div
                    id="full-ai-count"
                    class="full-ai-stat-value"
                >
                    -
                </div>

            </div>


            <div class="full-ai-stat">

                <div class="full-ai-stat-label">
                    Compound
                </div>

                <div
                    id="full-ai-compound-count"
                    class="full-ai-stat-value"
                >
                    -
                </div>

            </div>


            <div class="full-ai-stat">

                <div class="full-ai-stat-label">
                    Target
                </div>

                <div
                    id="full-ai-target-count"
                    class="full-ai-stat-value"
                >
                    -
                </div>

            </div>


        </div>


        <!-- Compound 선택 -->

        <div class="compound-selector">

            <label
                for="compound-select"
            >
Select a Compound to Analyze
            </label>


            <select
                id="compound-select"
            >

                <option value="">
Loading AI data...
                </option>

            </select>

        </div>


        <!-- 선택한 Compound -->

        <div
            id="selected-compound"
            class="selected-compound"
            style="display:none;"
        >

            <div
                id="selected-compound-name"
                class="selected-compound-name"
            ></div>


            <div
                id="selected-compound-id"
                class="selected-compound-id"
            ></div>

            <div
                id="top-target-summary"
                style="margin-top:12px;padding:14px 16px;border-radius:10px;background:#f4f8f1;border:1px solid #cddcc7;"
            ></div>

        </div>


        <!-- Target 결과 -->

        <div
            id="target-table-area"
            class="target-table-wrap"
            style="display:none;"
        >

            <table class="target-table">

                <thead>

                    <tr>

                        <th>
                            Target
                        </th>

                        <th>
                            Gene
                        </th>

                        <th>
                            AI-Predicted pChEMBL
                        </th>

                        <th>
                            Evidence
                        </th>

                        <th>
                            Target Role
                        </th>

                        <th>
                            Evidence Description
                        </th>

                    </tr>

                </thead>


                <tbody
                    id="full-target-body"
                >

                </tbody>

            </table>

        </div>


        <div
            id="full-ai-status"
            class="ai-detail-status"
        >

            Loading all AI data...

        </div>


        <div class="ai-detail-note">

            <strong>
                Important Interpretation Note:
            </strong>

            AI prediction values do not prove actual binding in experiments or
            therapeutic effects.

            This page presents screening and hypothesis-generation results for
            exploring candidate compounds and related targets.
            Screening / Hypothesis Generation Results.

        </div>

    </div>


    <div class="notice">

        These AI results are intended to identify candidate compounds and targets for
        <strong>Screening / Hypothesis Generation Results</strong>.

        They do not prove actual binding, therapeutic effects, or clinical efficacy.
        

    </div>

</div>


<!-- =======================================================
     Observed Distribution Map
     ======================================================= -->

<div class="card">

    <div class="card-header">

        <h2>
            Observed Distribution Data
        </h2>

        <p>
            iNaturalist and GBIF observation records are displayed on the map.
        </p>

    </div>


    <div class="map-wrap">

        <div id="map"></div>


        <div class="map-legend">

            <strong>Observation Data Sources</strong>

            <div class="legend-row">
                <span class="legend-dot legend-inat"></span>
                iNaturalist
            </div>

            <div class="legend-row">
                <span class="legend-dot legend-gbif"></span>
                GBIF
            </div>

            <div class="legend-row">
                <span class="legend-dot legend-other"></span>
                Other
            </div>

        </div>


        <div class="map-footer">

        <span id="distribution-status">

            Loading distribution data...

        </span>

    </div>

</div>


<div class="notice">
    <strong>
        Important Data Interpretation Notes
    </strong>

    <br>

    Points on the map represent locations recorded in public biodiversity observation data.
    These points do not necessarily indicate actual medicinal plant cultivation areas or
    areas where medicinal effects have been confirmed.

</div>


{% else %}


<!-- =======================================================
     Initial Search Screen
     ======================================================= -->

<div class="card">

    <div class="info">

        <div class="info-title">

            Search for a Medicinal Plant

        </div>


        <p>

            Enter a plant name or scientific name.

        </p>


        <p>

            Example: Ginseng · Panax ginseng

        </p>

    </div>

</div>


{% endif %}


</main>


<footer class="footer">

    GeoPharm · Medicinal Plant Analysis Platform

</footer>


<!-- =======================================================
     Leaflet
     ======================================================= -->

<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js">
</script>


<!-- =======================================================
     MarkerCluster
     ======================================================= -->

<script src="https://unpkg.com/leaflet.markercluster@1.5.3/dist/leaflet.markercluster.js">
</script>


<script>

// ==========================================================
// Plant ID
// ==========================================================

const plantId =

    {{ (plant.get(
        "Plant_ID",
        ""
    ) if plant else "")|tojson }};


// ==========================================================
// 자동완성
// ==========================================================

const searchInput =
    document.getElementById(
        "plant-search"
    );

const resolvedScientificNameInput =
    document.getElementById(
        "resolved-scientific-name"
    );

// ==========================================================
// Plant 분석 진행 화면
// ==========================================================

const plantAnalyzeButton =
    document.getElementById(
        "plant-analyze-button"
    );

const analysisLoading =
    document.getElementById(
        "analysis-loading"
    );

const plantSearchForm =
    searchInput
        ? searchInput.closest("form")
        : null;


if (
    plantSearchForm &&
    analysisLoading
) {

    plantSearchForm.addEventListener(
        "submit",
        function() {

            analysisLoading.style.display =
                "flex";

            if (plantAnalyzeButton) {

                plantAnalyzeButton.disabled =
                    true;

            }

        }
    );

}

const autocomplete =
    document.getElementById(
        "autocomplete"
    );


let searchTimer = null;


// ==========================================================
// 질병 자동완성
// ==========================================================

const diseaseSearchInput =
    document.getElementById(
        "disease-search"
    );

const diseaseAutocomplete =
    document.getElementById(
        "disease-autocomplete"
    );

let diseaseSearchTimer = null;


function showDiseaseSuggestions(
    diseases
) {

    if (!diseaseAutocomplete) {
        return;
    }


    diseaseAutocomplete.innerHTML = "";


    if (!diseases || diseases.length === 0) {

        diseaseAutocomplete.style.display = "none";

        return;

    }


    diseases.forEach(
        function(disease) {

            const item =
                document.createElement(
                    "div"
                );


            item.className =
                "autocomplete-item";


            item.innerHTML =
                '<div class="autocomplete-ko">' +
                escapeHtml(
                    disease.display || disease.name || ""
                ) +
                '</div>' +
                '<div class="autocomplete-sub">' +
                escapeHtml(
                    disease.name || ""
                ) +
                '</div>';


            item.addEventListener(
                "mousedown",
                function(event) {

                    event.preventDefault();

                    diseaseSearchInput.value =
                        disease.name ||
                        disease.display ||
                        "";

                    diseaseAutocomplete.style.display =
                        "none";

                    diseaseSearchInput
                        .closest("form")
                        .submit();

                }
            );


            diseaseAutocomplete.appendChild(
                item
            );

        }
    );


    diseaseAutocomplete.style.display =
        "block";

}


if (diseaseSearchInput) {

    diseaseSearchInput.addEventListener(
        "input",
        function() {

            const keyword =
                diseaseSearchInput.value.trim();


            clearTimeout(
                diseaseSearchTimer
            );


            if (keyword.length === 0) {

                diseaseAutocomplete.style.display =
                    "none";

                return;

            }


            diseaseSearchTimer =
                setTimeout(
                    function() {

                        fetch(
                            "/api/disease-search?q=" +
                            encodeURIComponent(
                                keyword
                            )
                        )
                        .then(
                            function(response) {
                                return response.json();
                            }
                        )
                        .then(
                            function(data) {
                                showDiseaseSuggestions(data);
                            }
                        )
                        .catch(
                            function(error) {
                                console.error(error);
                                diseaseAutocomplete.style.display =
                                    "none";
                            }
                        );

                    },
                    180
                );

        }
    );

}


function showSuggestions(
    plants
) {

    autocomplete.innerHTML = "";


    if (
        !plants ||
        plants.length === 0
    ) {

        autocomplete.innerHTML =
            '<div class="autocomplete-empty">' +
            'No matching plants were found.' +
            '</div>';


        autocomplete.style.display =
            "block";


        return;

    }


    plants.forEach(
        function(plant) {

            const item =
                document.createElement(
                    "div"
                );


            item.className =
                "autocomplete-item";


            const ko =
                plant.ko || "";


            const english =
                plant.english || "";


            const scientific =
                plant.scientific || "";


            item.innerHTML =

                 '<div class="autocomplete-ko">' +
                 escapeHtml(english) +
                   '</div>' +

                 '<div class="autocomplete-sub">' +
                  escapeHtml(scientific) +
                     '</div>';


            item.addEventListener(
                "mousedown",
                function(event) {

                    event.preventDefault();

                    searchInput.value =
                        english;

                    if (plant.external_candidate) {
                        resolvedScientificNameInput.name =
                            "scientific_name";
                        resolvedScientificNameInput.value =
                            scientific;
                        resolvedScientificNameInput.style.display =
                            "block";
                        autocomplete.style.display = "none";
                        return;
                    }

                    resolvedScientificNameInput.removeAttribute("name");
                    resolvedScientificNameInput.value = "";
                    resolvedScientificNameInput.style.display = "none";


                    autocomplete.style.display =
                        "none";


                    searchInput
                        .closest("form")
                        .submit();

                }
            );


            autocomplete.appendChild(
                item
            );

        }
    );


    autocomplete.style.display =
        "block";

}


if (searchInput) {

    searchInput.addEventListener(
        "input",
        function() {

            const keyword =
                searchInput.value.trim();

            resolvedScientificNameInput.removeAttribute("name");
            resolvedScientificNameInput.value = "";
            resolvedScientificNameInput.style.display = "none";


            clearTimeout(
                searchTimer
            );


            if (
                keyword.length === 0
            ) {
                // 검색어가 없어도 등록 Plant 목록을 요청합니다.
            }


            searchTimer =
                setTimeout(
                    function() {

                        fetch(
                            "/api/plant-search?q=" +
                            encodeURIComponent(
                                keyword
                            )
                        )

                        .then(
                            function(response) {

                                return response.json();

                            }
                        )

                        .then(
                            function(data) {

                                if (data && data.length) {
                                    showSuggestions(data);
                                    return;
                                }

                                if (keyword.length < 3) {
                                    showSuggestions(data);
                                    return;
                                }

                                autocomplete.innerHTML =
                                    '<div class="autocomplete-empty">' +
                                    'Looking up scientific names…' +
                                    '</div>';
                                autocomplete.style.display = "block";

                                fetch(
                                    "/api/plant-name-resolve?q=" +
                                    encodeURIComponent(keyword)
                                )
                                .then(function(response) {
                                    if (!response.ok) {
                                        throw new Error("Plant name lookup failed");
                                    }
                                    return response.json();
                                })
                                .then(function(candidates) {
                                    if (searchInput.value.trim() !== keyword) {
                                        return;
                                    }
                                    if (Array.isArray(candidates) && candidates.length === 1) {
                                        const candidate = candidates[0];
                                        resolvedScientificNameInput.name =
                                            "scientific_name";
                                        resolvedScientificNameInput.value =
                                            candidate.scientific || "";
                                        resolvedScientificNameInput.style.display =
                                            "block";
                                        autocomplete.style.display = "none";
                                        return;
                                    }
                                    showSuggestions(candidates);
                                })
                                .catch(function(error) {
                                    console.error(error);
                                    if (searchInput.value.trim() === keyword) {
                                        showSuggestions([]);
                                    }
                                });

                            }
                        )

                        .catch(
                            function(error) {

                                console.error(
                                    error
                                );

                                autocomplete.style.display =
                                    "none";

                            }
                        );

                    },
                    450
                );

        }
    );


    searchInput.addEventListener(
        "focus",
        function() {

            const keyword =
                searchInput.value.trim();


            searchInput.dispatchEvent(
                new Event(
                    "input"
                )
            );

        }
    );

}


document.addEventListener(
    "click",
    function(event) {

        if (
            !event.target.closest(
                ".search-box"
            )
        ) {

            if (autocomplete) {

                autocomplete.style.display =
                    "none";

            }

            if (diseaseAutocomplete) {

                diseaseAutocomplete.style.display =
                    "none";

            }

        }

    }
);


// ==========================================================
// HTML 안전 처리
// ==========================================================

function escapeHtml(
    value
) {

    if (
        value === null ||
        value === undefined
    ) {

        return "";

    }


    return String(value)

        .replace(
            /&/g,
            "&amp;"
        )

        .replace(
            /</g,
            "&lt;"
        )

        .replace(
            />/g,
            "&gt;"
        )

        .replace(
            /"/g,
            "&quot;"
        )

        .replace(
            /'/g,
            "&#039;"
        );

}


// ==========================================================
// 숫자 표시
// ==========================================================

function formatScore(
    value
) {

    if (
        value === null ||
        value === undefined ||
        value === ""
    ) {

        return "-";

    }


    const number =
        Number(value);


    if (
        !Number.isFinite(number)
    ) {

        return "-";

    }


    return number.toFixed(3);

}


// ==========================================================
// 주요 AI 후보 10개
// ==========================================================

function loadAIDetail() {

    const detailBox =
        document.getElementById(
            "ai-detail"
        );


    const status =
        document.getElementById(
            "ai-detail-status"
        );


    const body =
        document.getElementById(
            "ai-detail-body"
        );


    if (
        !detailBox ||
        !status ||
        !body
    ) {

        return;

    }


    if (
        detailBox.style.display === "block"
    ) {

        detailBox.style.display =
            "none";

        return;

    }


    detailBox.style.display =
        "block";


    status.textContent =
        "Loading top AI candidate data...";


    body.innerHTML = "";


    fetch(
        "/api/ai-detail/" +
        encodeURIComponent(
            plantId
        )
    )

    .then(
        function(response) {

            if (!response.ok) {

                throw new Error(
                    "Failed to load AI detail data."
                );

            }


            return response.json();

        }
    )

    .then(
        function(data) {

            const records =
                Array.isArray(
                    data.records
                )
                    ? data.records
                    : [];


            if (
                records.length === 0
            ) {

                status.textContent =
                    "No top AI candidate data is linked to this plant.";

                return;

            }


            status.textContent =
                "Top AI Candidate Compounds " +
                records.length.toLocaleString() +
                " items";


            records.forEach(
                function(record, index) {

                    const row =
                        document.createElement(
                            "tr"
                        );


                    const compound =
                        record.Compound_Name ||
                        "-";


                    const chembl =
                        record.ChEMBL_ID ||
                        "-";


                    const uniprot =
                        record.UniProt_ID ||
                        "-";


                    const predicted =
                        formatScore(
                            record.Predicted_pChEMBL
                        );


                    const evidence =
                        record.Target_Evidence ||
                        "-";


                    const role =
                        record.Target_Role ||
                        "-";


                    row.innerHTML =

                        "<td>" +
                        escapeHtml(
                            index + 1
                        ) +
                        "</td>" +

                        '<td class="target-name">' +
                        escapeHtml(compound) +
                        "</td>" +

                        "<td>" +
                        escapeHtml(chembl) +
                        "</td>" +

                        "<td>" +
                        escapeHtml(uniprot) +
                        "</td>" +

                        '<td class="predicted-score">' +
                        escapeHtml(predicted) +
                        "</td>" +

                        '<td><span class="evidence-badge">' +
                        escapeHtml(evidence) +
                        "</span></td>" +

                        '<td class="role-text">' +
                        escapeHtml(role) +
                        "</td>";


                    body.appendChild(
                        row
                    );

                }
            );

        }
    )

    .catch(
        function(error) {

            console.error(
                error
            );


            status.textContent =
                "An error occurred while loading top AI data.";

        }
    );

}


// ==========================================================
// 전체 AI 데이터
// ==========================================================

let fullAIRecords = [];


let fullAICompounds = [];


function loadFullAIData() {

    const status =
        document.getElementById(
            "full-ai-status"
        );


    if (!status) {

        return;

    }


    status.textContent =
        "Loading all AI data...";


    fetch(
        "/api/ai-full/" +
        encodeURIComponent(
            plantId
        )
    )

    .then(
        function(response) {

            if (!response.ok) {

                throw new Error(
                    "Failed to load all AI data."
                );

            }


            return response.json();

        }
    )

    .then(
        function(data) {


            fullAIRecords =
                Array.isArray(
                    data.records
                )
                    ? data.records
                    : [];


            fullAICompounds = [];


            const compoundMap =
                new Map();


            fullAIRecords.forEach(
                function(record) {

                    const compound =
                        String(
                            record.Compound_Name || ""
                        ).trim();


                    if (
                        compound === ""
                    ) {

                        return;

                    }


                    if (
                        !compoundMap.has(
                            compound
                        )
                    ) {

                        compoundMap.set(
                            compound,
                            {
                                name: compound,

                                chembl:
                                    record.ChEMBL_ID ||
                                    "",

                                maxScore:
                                    Number(
                                        record.Predicted_pChEMBL || 0
                                    )
                            }
                        );

                    }

                }
            );


            fullAICompounds =
                Array.from(
                    compoundMap.values()
                );


            // ------------------------------------------------
            // 통계
            // ------------------------------------------------

            const countElement =
                document.getElementById(
                    "full-ai-count"
                );


            const compoundCountElement =
                document.getElementById(
                    "full-ai-compound-count"
                );


            const targetCountElement =
                document.getElementById(
                    "full-ai-target-count"
                );


            if (countElement) {

                countElement.textContent =
                    Number(
                        data.count || 0
                    ).toLocaleString();

            }


            if (compoundCountElement) {

                compoundCountElement.textContent =
                    Number(
                        data.compound_count || 0
                    ).toLocaleString();

            }


            if (targetCountElement) {

                targetCountElement.textContent =
                    Number(
                        data.target_count || 0
                    ).toLocaleString();

            }


            // ------------------------------------------------
            // Compound 선택 목록
            // ------------------------------------------------

            const select =
                document.getElementById(
                    "compound-select"
                );


            if (!select) {

                return;

            }


            select.innerHTML = "";


            if (
                fullAICompounds.length === 0
            ) {

                const option =
                    document.createElement(
                        "option"
                    );


                option.value = "";


                option.textContent =
                    "No AI candidate compounds available.";


                select.appendChild(
                    option
                );


                status.textContent =
                    "No AI candidate data is available.";


                return;

            }


            const firstOption =
                document.createElement(
                    "option"
                );


            firstOption.value = "";


            firstOption.textContent =
                "Select a compound";


            select.appendChild(
                firstOption
            );


            fullAICompounds.forEach(
                function(compound) {

                    const option =
                        document.createElement(
                            "option"
                        );


                    option.value =
                        compound.name;


                    option.textContent =

                        compound.name +

                        (
                            compound.chembl
                                ? " · " +
                                  compound.chembl
                                : ""
                        ) +

                        " · Highest AI Prediction " +
                        Number(
                            compound.maxScore || 0
                        ).toFixed(3);


                    select.appendChild(
                        option
                    );

                }
            );


            status.textContent =
"Total AI candidate records: " +
                Number(
                    data.count || 0
                ).toLocaleString() +
" records loaded. " +
"Select a compound to view predictions for each target.";

        }
    )

    .catch(
        function(error) {

            console.error(
                error
            );


            status.textContent =
                "Failed to load all AI data.";

        }
    );

}


// ==========================================================
// Compound 선택
// ==========================================================

function showSelectedCompound(
    compoundName
) {

    const selectedBox =
        document.getElementById(
            "selected-compound"
        );


    const selectedName =
        document.getElementById(
            "selected-compound-name"
        );


    const selectedId =
        document.getElementById(
            "selected-compound-id"
        );


    const targetArea =
        document.getElementById(
            "target-table-area"
        );


    const targetBody =
        document.getElementById(
            "full-target-body"
        );


    if (
        !selectedBox ||
        !selectedName ||
        !selectedId ||
        !targetArea ||
        !targetBody
    ) {

        return;

    }


    if (
        !compoundName
    ) {

        selectedBox.style.display =
            "none";


        targetArea.style.display =
            "none";


        targetBody.innerHTML =
            "";


        return;

    }


    const records =
        fullAIRecords.filter(
            function(record) {

                return String(
                    record.Compound_Name || ""
                ).trim()
                ===
                String(
                    compoundName
                ).trim();

            }
        );


    if (
        records.length === 0
    ) {

        selectedBox.style.display =
            "block";


        selectedName.textContent =
            compoundName;


        selectedId.textContent =
            "No AI prediction data was found for this compound.";


        targetArea.style.display =
            "none";


        return;

    }


    // --------------------------------------------------------
    // 예측값 높은 순
    // --------------------------------------------------------

    records.sort(
        function(a, b) {

            return Number(
                b.Predicted_pChEMBL || 0
            )
            -
            Number(
                a.Predicted_pChEMBL || 0
            );

        }
    );


    selectedBox.style.display =
        "block";


    selectedName.textContent =
        compoundName;


    const chembl =
        records[0].ChEMBL_ID || "-";


    selectedId.textContent =
        "ChEMBL ID: " +
        chembl;


    const topTargetBox =
        document.getElementById(
            "top-target-summary"
        );


    if (topTargetBox && records.length > 0) {

        const topTarget = records[0];

        const topProtein =
            topTarget.Protein_Name || "-";

        const topGene =
            topTarget.Gene_Name || "-";

        const topScore =
            formatScore(
                topTarget.Predicted_pChEMBL
            );

        const topEvidence =
            topTarget.Target_Evidence || "-";

        topTargetBox.innerHTML =
            '<div style="font-size:15px;font-weight:bold;color:#31543b;margin-bottom:8px;">Top-Ranked AI-Predicted Target</div>' +
            '<div style="font-size:18px;font-weight:bold;color:#243b2b;">' +
                escapeHtml(topProtein) +
            '</div>' +
            '<div style="margin-top:4px;color:#657065;font-size:13px;">Gene: ' +
                escapeHtml(topGene) +
            '</div>' +
            '<div style="margin-top:8px;font-size:16px;font-weight:bold;">AI-Predicted pChEMBL: ' +
                escapeHtml(topScore) +
            '</div>' +
            '<div style="margin-top:5px;font-size:13px;">Evidence Level: ' +
                escapeHtml(topEvidence) +
            '</div>';

    }


    targetBody.innerHTML =
        "";


    records.forEach(
        function(record) {

            const row =
                document.createElement(
                    "tr"
                );


            const protein =
                record.Protein_Name ||
                "-";


            const gene =
                record.Gene_Name ||
                "-";


            const predicted =
                formatScore(
                    record.Predicted_pChEMBL
                );


            const evidence =
                record.Target_Evidence ||
                "-";


            const role =
                record.Target_Role ||
                "-";


            const note =
                record.Evidence_Note ||
                "-";


            row.innerHTML =

                '<td>' +

                    '<div class="target-name">' +

                        escapeHtml(
                            protein
                        ) +

                    "</div>" +

                    '<div class="target-gene">' +

                        escapeHtml(
                            gene
                        ) +

                    "</div>" +

                "</td>" +

                "<td>" +

                    escapeHtml(
                        gene
                    ) +

                "</td>" +

                '<td class="predicted-score">' +

                    escapeHtml(
                        predicted
                    ) +

                "</td>" +

                '<td>' +

                    '<span class="evidence-badge">' +

                        escapeHtml(
                            evidence
                        ) +

                    "</span>" +

                "</td>" +

                '<td class="role-text">' +

                    escapeHtml(
                        role
                    ) +

                "</td>" +

                '<td class="note-text">' +

                    escapeHtml(
                        note
                    ) +

                "</td>";


            targetBody.appendChild(
                row
            );

        }
    );


    targetArea.style.display =
        "block";

}


// ==========================================================
// Compound 선택 이벤트
// ==========================================================

const compoundSelect =
    document.getElementById(
        "compound-select"
    );


if (compoundSelect) {

    compoundSelect.addEventListener(
        "change",
        function() {

            showSelectedCompound(
                compoundSelect.value
            );

        }
    );

}


// ==========================================================
// Leaflet 지도
// ==========================================================

{% if plant %}

const map =
    L.map(
        "map",
        {
            worldCopyJump: false,

            minZoom: 3,

            maxZoom: 18
        }
    ).setView(
        [
            36.0,
            128.0
        ],
        4
    );


// ==========================================================
// 영어 지명 지도
// ==========================================================

L.tileLayer(

    "https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}",

    {

        maxZoom: 18,

        noWrap: true,

        attribution:
            "Tiles &copy; Esri | " +
            "Sources: Esri, DeLorme, HERE, " +
            "USGS, Intermap, iPC, NRCAN, " +
            "Esri Japan, METI, Esri China (Hong Kong), " +
            "Esri (Thailand), MapmyIndia, TomTom"

    }

).addTo(map);


map.setMaxBounds(
    [
        [
            -85,
            -180
        ],
        [
            85,
            180
        ]
    ]
);


// ==========================================================
// MarkerCluster
// ==========================================================

const markerCluster =
    L.markerClusterGroup({

        showCoverageOnHover:
            false,

        spiderfyOnMaxZoom:
            true,

        disableClusteringAtZoom:
            8,

        maxClusterRadius:
            45,

        zoomToBoundsOnClick:
            true,

        chunkedLoading:
            true,

        chunkInterval:
            100,

        chunkDelay:
            25,

        removeOutsideVisibleBounds:
            true

    });


// ==========================================================
// 숫자
// ==========================================================

function getNumber(
    record,
    names
) {

    for (
        const name of names
    ) {

        if (
            Object.prototype.hasOwnProperty.call(
                record,
                name
            )
        ) {

            const value =
                record[name];


            if (
                value !== null &&
                value !== undefined &&
                String(value).trim() !== ""
            ) {

                const number =
                    Number(value);


                if (
                    Number.isFinite(number)
                ) {

                    return number;

                }

            }

        }

    }


    return null;

}


// ==========================================================
// 값
// ==========================================================

function getValue(
    record,
    names
) {

    for (
        const name of names
    ) {

        if (
            Object.prototype.hasOwnProperty.call(
                record,
                name
            )
        ) {

            const value =
                record[name];


            if (
                value !== null &&
                value !== undefined &&
                String(value).trim() !== ""
            ) {

                return value;

            }

        }

    }


    return "";

}


// ==========================================================
// 지도 마커
// ==========================================================

function makeMarker(
    record
) {

    const lat =
        getNumber(
            record,
            [
                "latitude",
                "Latitude",
                "lat",
                "Lat",
                "decimalLatitude",
                "Decimal_Latitude"
            ]
        );


    const lon =
        getNumber(
            record,
            [
                "longitude",
                "Longitude",
                "lon",
                "Lon",
                "decimalLongitude",
                "Decimal_Longitude"
            ]
        );


    if (
        lat === null ||
        lon === null
    ) {

        return null;

    }


    if (
        lat < -90 ||
        lat > 90 ||
        lon < -180 ||
        lon > 180
    ) {

        return null;

    }


    const source =
        String(
            getValue(
                record,
                [
                    "Source",
                    "source",
                    "Dataset",
                    "dataset"
                ]
            ) || "Other"
        );


    let markerClass =
        "marker-other";


    if (
        source.toLowerCase()
            .includes("inat") ||

        source.toLowerCase()
            .includes("naturalist")
    ) {

        markerClass =
            "marker-inat";

    }

    else if (
        source.toLowerCase()
            .includes("gbif")
    ) {

        markerClass =
            "marker-gbif";

    }


    const icon =
        L.divIcon({

            className: "",

            html:
                '<div class="marker-dot ' +
                markerClass +
                '"></div>',

            iconSize:
                [
                    12,
                    12
                ],

            iconAnchor:
                [
                    6,
                    6
                ],

            popupAnchor:
                [
                    0,
                    -6
                ]

        });


    const recordId =
        getValue(
            record,
            [
                "Record_ID",
                "record_id",
                "Occurrence_ID",
                "occurrenceID",
                "GBIF_ID",
                "iNaturalist_ID"
            ]
        );


    const country =
        getValue(
            record,
            [
                "Country",
                "country",
                "Country_Name",
                "countryCode"
            ]
        );


    const place =
        getValue(
            record,
            [
                "Place",
                "place",
                "Locality",
                "locality",
                "Location",
                "location"
            ]
        );


    const eventDate =
        getValue(
            record,
            [
                "Event_Date",
                "eventDate",
                "Date",
                "date"
            ]
        );


    const quality =
        getValue(
            record,
            [
                "Quality",
                "quality",
                "Coordinate_Quality",
                "coordinateQuality"
            ]
        );


    const sourceUrl =
        getValue(
            record,
            [
                "Source_URL",
                "source_url",
                "URL",
                "url",
                "Link",
                "link"
            ]
        );


    let html = "";


    html +=
        "<strong>GeoPharm Observation Record</strong><br><br>";


    html +=
        "<strong>Source:</strong> " +
        escapeHtml(source) +
        "<br>";


    if (recordId) {

        html +=
            "<strong>Record ID:</strong> " +
            escapeHtml(recordId) +
            "<br>";

    }


    if (country) {

        html +=
            "<strong>Country:</strong> " +
            escapeHtml(country) +
            "<br>";

    }


    if (place) {

        html +=
            "<strong>Place:</strong> " +
            escapeHtml(place) +
            "<br>";

    }


    if (eventDate) {

        html +=
            "<strong>Event Date:</strong> " +
            escapeHtml(eventDate) +
            "<br>";

    }


    if (quality) {

        html +=
            "<strong>Quality:</strong> " +
            escapeHtml(quality) +
            "<br>";

    }


    html +=
        "<strong>Latitude:</strong> " +
        lat.toFixed(5) +
        "<br>";


    html +=
        "<strong>Longitude:</strong> " +
        lon.toFixed(5) +
        "<br>";


    if (sourceUrl) {

        html +=
            '<br><a href="' +
            escapeHtml(sourceUrl) +
            '" target="_blank" rel="noopener noreferrer">' +
            "View Original Record" +
            "</a>";

    }


    const marker =
        L.marker(
            [
                lat,
                lon
            ],
            {
                icon: icon
            }
        );


    marker.bindPopup(
        html,
        {
            maxWidth: 340
        }
    );


    return marker;

}


// ==========================================================
// 분포 데이터 불러오기
// ==========================================================

fetch(
    "/api/distribution/" +
    encodeURIComponent(
        plantId
    )
)

.then(
    function(response) {

        if (!response.ok) {

            throw new Error(
                "Failed to load distribution data."
            );

        }


        return response.json();

    }
)

.then(
    function(data) {

        const records =
            Array.isArray(
                data.records
            )
                ? data.records
                : [];


        let validCount = 0;


        const bounds = [];


        for (
            const record of records
        ) {

            const marker =
                makeMarker(
                    record
                );


            if (!marker) {

                continue;

            }


            markerCluster.addLayer(
                marker
            );


            const lat =
                getNumber(
                    record,
                    [
                        "latitude",
                        "Latitude",
                        "lat",
                        "Lat",
                        "decimalLatitude",
                        "Decimal_Latitude"
                    ]
                );


            const lon =
                getNumber(
                    record,
                    [
                        "longitude",
                        "Longitude",
                        "lon",
                        "Lon",
                        "decimalLongitude",
                        "Decimal_Longitude"
                    ]
                );


            if (
                lat !== null &&
                lon !== null
            ) {

                bounds.push(
                    [
                        lat,
                        lon
                    ]
                );

            }


            validCount++;

        }


        map.addLayer(
            markerCluster
        );


        if (
            bounds.length > 0
        ) {

            map.fitBounds(
                bounds,
                {
                    padding:
                        [
                            30,
                            30
                        ],

                    maxZoom:
                        8
                }
            );

        }


        const status =
            document.getElementById(
                "distribution-status"
            );


        if (status) {

            status.textContent =

                "Total observation coordinates " +

                records.length
                    .toLocaleString() +

                " · Valid coordinates " +

                validCount
                    .toLocaleString() +

                " · Clusters displayed";

        }

    }
)

.catch(
    function(error) {

        console.error(
            error
        );


        const status =
            document.getElementById(
                "distribution-status"
            );


        if (status) {

            status.textContent =
                "Failed to load distribution data.";

        }

    }
);


// ==========================================================
// 전체 AI 데이터도 함께 준비
// ==========================================================

loadFullAIData();


{% endif %}

</script>


</body>

</html>
"""


# ============================================================
# 메인 페이지
# ============================================================

@app.route(
    "/",
    methods=["GET"]
)
def index():

    global T2D_PLANTS, T2D_TARGETS, T2D_CANDIDATES

    T2D_PLANTS, T2D_TARGETS, T2D_CANDIDATES = load_t2d_data()

    keyword = request.args.get(
        "plant",
        ""
    ).strip()
    selected_scientific_name = request.args.get(
        "scientific_name",
        ""
    ).strip()

    plant = None

    name_candidates = []

    selected_t2d_score = None
    pipeline_error = ""


    if keyword and plant is None:
        from src.resolve_plant_name import (
            find_registered_plant,
        )

        if selected_scientific_name and ENABLE_PLANT_PIPELINE:
            from src.resolve_plant_name import run_new_plant

            try:
                plant_id = run_new_plant(keyword, selected_scientific_name)
            except Exception:
                app.logger.exception(
                    "New plant pipeline failed for %r (%r)",
                    keyword,
                    selected_scientific_name,
                )
                pipeline_error = (
                    "New plant registration or AI analysis failed. "
                    "Check the server terminal for the error details."
                )
                plant_id = None

            if plant_id:
                T2D_PLANTS, T2D_TARGETS, T2D_CANDIDATES = load_t2d_data()
                plant = {
                    "Plant_ID": plant_id,
                    "Common_Name_KO": "",
                    "English_Name": keyword,
                    "Scientific_Name": selected_scientific_name,
                }

        else:
            registered = find_registered_plant(keyword)

            if registered:
                plant = registered

            elif ENABLE_PLANT_PIPELINE:
                from src.resolve_plant_name import (
                    search_plant_name,
                    resolve_candidates,
                    resolve_inaturalist_candidates,
                    run_new_plant,
                )

                try:
                    results = search_plant_name(keyword)
                    resolved = resolve_candidates(results)
                    inat_resolved = resolve_inaturalist_candidates(keyword)
                except Exception:
                    app.logger.exception(
                        "Plant name lookup failed for %r", keyword
                    )
                    resolved = []
                    inat_resolved = []
                    pipeline_error = (
                        "Plant name lookup failed. Check your internet "
                        "connection and the server terminal."
                    )

                if inat_resolved:
                    best_inat = inat_resolved[0]

                    if best_inat.get("score", 0) >= 100:
                        resolved = [best_inat]

                if len(resolved) == 1:

                 selected_scientific_name = (
                 resolved[0]["scientific_name"]
                  )

                 try:
                    plant_id = run_new_plant(
                        keyword,
                        selected_scientific_name,
                    )
                 except Exception:
                    app.logger.exception(
                        "New plant pipeline failed for %r (%r)",
                        keyword,
                        selected_scientific_name,
                    )
                    pipeline_error = (
                        "New plant registration or AI analysis failed. "
                        "Check the server terminal for the error details."
                    )
                    plant_id = None

                 if plant_id:
                    T2D_PLANTS, T2D_TARGETS, T2D_CANDIDATES = load_t2d_data()
                    plant = {
                        "Plant_ID": plant_id,
                        "Common_Name_KO": "",
                        "English_Name": keyword,
                        "Scientific_Name": selected_scientific_name,
                    }

                elif len(resolved) > 1:
                    name_candidates = resolved

    # 검색한 Plant의 T2D 우선Rank 점수를 찾아서
    # 메인 화면에 표시합니다.
    if (
        plant
        and not T2D_PLANTS.empty
        and "Plant_ID" in T2D_PLANTS.columns
    ):

        plant_id = str(
            plant.get(
                "Plant_ID",
                ""
            )
        )

        selected_rows = T2D_PLANTS[
            T2D_PLANTS["Plant_ID"].astype(str)
            == plant_id
        ]

        if not selected_rows.empty:

            selected_t2d_score = (
                selected_rows.iloc[0].to_dict()
            )


    return render_template_string(

        HTML,

        keyword=keyword,

        plant=plant,

        name_candidates=name_candidates,

        pipeline_enabled=ENABLE_PLANT_PIPELINE,

        pipeline_error=pipeline_error,

        disease_keyword="",

        T2D_PLANTS=T2D_PLANTS,

        T2D_TARGETS=T2D_TARGETS,

        T2D_CANDIDATES=T2D_CANDIDATES,

        selected_t2d_score=selected_t2d_score

    )


# ============================================================
# 서버 실행
# ============================================================

if __name__ == "__main__":
    # Flask's built-in server is for local development only. Production runs
    # through Gunicorn (see render.yaml), with debug disabled by default.
    is_debug = os.environ.get("FLASK_DEBUG", "false").strip().lower() in {
        "1", "true", "yes", "on"
    }
    app.run(
        debug=is_debug,
        host=os.environ.get("HOST", "127.0.0.1"),
        port=int(os.environ.get("PORT", "5000")),
    )
