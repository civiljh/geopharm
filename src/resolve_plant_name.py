import requests
import os
import pandas as pd


GBIF_SEARCH_URL = "https://api.gbif.org/v1/species/search"
GBIF_MATCH_URL = "https://api.gbif.org/v1/species/match"
INATURALIST_TAXA_URL = "https://api.inaturalist.org/v1/taxa"

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PLANT_FILE = os.path.join(
    BASE_DIR,
    "data",
    "raw",
    "medicinal_plants.csv",
)

def search_inaturalist_name(english_name):
    params = {
        "q": english_name,
        "rank": "species",
        "per_page": 10,
    }

    response = requests.get(
        INATURALIST_TAXA_URL,
        params=params,
        timeout=20,
    )

    response.raise_for_status()

    data = response.json()
    results = []

    for item in data.get("results", []):
        scientific_name = item.get("name")

        if not scientific_name:
            continue

        if item.get("rank") != "species":
            continue

        if item.get("iconic_taxon_name") != "Plantae":
            continue

        results.append({
            "scientific_name": scientific_name,
            "preferred_common_name": item.get(
                "preferred_common_name",
                "",
            ),
            "matched_term": item.get(
                "matched_term",
                "",
            ),
            "rank": item.get("rank", ""),
        })

    return results

def score_inaturalist_candidates(
    english_name,
    candidates,
):
    keyword = str(english_name).strip().lower()

    scored = []

    for item in candidates:
        preferred = str(
            item.get("preferred_common_name", "")
        ).strip().lower()

        matched_term = str(
            item.get("matched_term", "")
        ).strip().lower()

        score = 0

        if preferred == keyword:
            score += 100

        if matched_term == keyword:
            score += 80

        if keyword in preferred:
            score += 40

        if keyword in matched_term:
            score += 30

        item = item.copy()
        item["score"] = score

        scored.append(item)

    scored.sort(
        key=lambda x: x["score"],
        reverse=True,
    )

    return scored

def resolve_inaturalist_candidates(
    english_name,
):
    try:
        candidates = search_inaturalist_name(
            english_name
        )
    except requests.RequestException:
        return []

    scored = score_inaturalist_candidates(
        english_name,
        candidates,
    )

    resolved = []

    for item in scored:
        scientific_name = item.get(
            "scientific_name"
        )

        if not scientific_name:
            continue

        try:
            matched = match_scientific_name(
                scientific_name
            )
        except requests.RequestException:
            continue

        if matched.get("match_type") != "EXACT":
            continue

        if matched.get("rank") != "SPECIES":
            continue

        if matched.get("kingdom") != "Plantae":
            continue

        if not matched.get("scientific_name"):
            continue

        resolved.append({
            "scientific_name": matched[
                "scientific_name"
            ],
            "status": matched.get(
                "status",
                "",
            ),
            "confidence": matched.get(
                "confidence"
            ),
            "match_type": matched.get(
                "match_type",
                "",
            ),
            "species_key": matched.get(
                "species_key"
            ),
            "source": "iNaturalist",
            "score": item.get(
                "score",
                0,
            ),
            "preferred_common_name": item.get(
                "preferred_common_name",
                "",
            ),
        })

    unique = {}

    for item in resolved:
        name = item["scientific_name"]

        if name not in unique:
            unique[name] = item

    return list(unique.values())

def find_registered_plant(english_name):
    if not os.path.exists(PLANT_FILE):
        return None

    df = pd.read_csv(PLANT_FILE)

    if "English_Name" not in df.columns:
        return None

    keyword = str(english_name).strip().lower()

    if not keyword:
        return None

    matches = df[
        df["English_Name"]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.lower()
        == keyword
    ]

    if matches.empty:
        return None

    return matches.iloc[0].to_dict()

def match_scientific_name(scientific_name):
    params = {
        "name": scientific_name,
    }

    response = requests.get(
        GBIF_MATCH_URL,
        params=params,
        timeout=20,
    )

    response.raise_for_status()

    data = response.json()

    return {
        "scientific_name": data.get("canonicalName"),
        "status": data.get("status", ""),
        "rank": data.get("rank", ""),
        "confidence": data.get("confidence"),
        "match_type": data.get("matchType", ""),
        "species_key": data.get("speciesKey"),
            "kingdom": data.get("kingdom", ""),
    }

def search_plant_name(english_name):
    params = {
        "q": english_name,
        "qField": "VERNACULAR",
        "rank": "SPECIES",
        "limit": 10,
    }

    response = requests.get(
        GBIF_SEARCH_URL,
        params=params,
        timeout=20,
    )

    response.raise_for_status()

    data = response.json()

    results = []

    for item in data.get("results", []):
        scientific_name = item.get("canonicalName")

        if not scientific_name:
            continue

        results.append({
            "scientific_name": scientific_name,
            "status": item.get("status", ""),
            "rank": item.get("rank", ""),
            "key": item.get("key"),
        })

    return results


def resolve_candidates(results):
    resolved = []

    for item in results:
        scientific_name = item.get("scientific_name")

        if not scientific_name:
            continue

        try:
            matched = match_scientific_name(scientific_name)
        except requests.RequestException:
            continue

        if matched.get("match_type") != "EXACT":
            continue

        if matched.get("rank") != "SPECIES":
            continue

        if matched.get("kingdom") != "Plantae":
            continue

        if not matched.get("scientific_name"):
            continue

        resolved.append({
            "scientific_name": matched["scientific_name"],
            "status": matched.get("status", ""),
            "confidence": matched.get("confidence"),
            "match_type": matched.get("match_type", ""),
            "species_key": matched.get("species_key"),
        })

    unique = {}

    for item in resolved:
        name = item["scientific_name"]
        unique[name] = item

    return list(unique.values())

def run_new_plant(english_name, scientific_name):
    import sys

    sys.path.insert(0, os.path.join(BASE_DIR, "src"))

    import run_new_plant as pipeline

    return pipeline.main(
        common_name_ko="",
        english_name=english_name,
        scientific_name=scientific_name,
    )

def choose_candidate(candidates):
    if not candidates:
        return None

    if len(candidates) == 1:
        return candidates[0]

    print()
    print("여러 학명이 발견되었습니다.")
    print("사용할 식물을 선택하세요.")

    for i, item in enumerate(candidates, start=1):
        print(f"{i}. {item['scientific_name']}")

    while True:
        choice = input("번호를 입력하세요: ").strip()

        if not choice.isdigit():
            print("숫자를 입력해주세요.")
            continue

        index = int(choice)

        if 1 <= index <= len(candidates):
            return candidates[index - 1]

        print("올바른 번호를 입력해주세요.")

if __name__ == "__main__":
    name = input("영어 식물명: ").strip()

    registered = find_registered_plant(name)

    if registered:
        print()
        print("기존 등록 식물입니다.")
        print(f"Plant_ID: {registered['Plant_ID']}")
        print(f"한국어 이름: {registered['Common_Name_KO']}")
        print(f"영어 이름: {registered['English_Name']}")
        print(f"학명: {registered['Scientific_Name']}")

    else:
        results = search_plant_name(name)
        gbif_resolved = resolve_candidates(results)

        inat_resolved = resolve_inaturalist_candidates(name)

        resolved = []

        if inat_resolved:
            best_inat = inat_resolved[0]

            if best_inat.get("score", 0) >= 100:
                resolved.append(best_inat)

        if not resolved:
            resolved = gbif_resolved

        if not resolved:
            resolved = inat_resolved

        if resolved:
            print()
            print("식물 후보:")

            for i, item in enumerate(resolved, start=1):
                print(
                    f"{i}. {item['scientific_name']} "
                    f"(status={item['status']}, "
                    f"confidence={item['confidence']}, "
                    f"match={item['match_type']})"
                )

            selected = choose_candidate(resolved)

            if selected:
                print()
                print("선택한 식물 정보:")
                print(f"영어 이름: {name}")
                print(f"학명: {selected['scientific_name']}")
            else:
                print()
                print("사용할 학명을 찾지 못했습니다.")

        else:
            print()
            print("사용할 식물 후보를 찾지 못했습니다.")