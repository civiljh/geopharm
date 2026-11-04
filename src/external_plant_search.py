import pandas as pd
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote


OUTPUT_FILE = "data/raw/external_plant_compounds.csv"

GBIF_MATCH_URL = "https://api.gbif.org/v1/species/match"
GBIF_SYNONYM_URL = "https://api.gbif.org/v1/species/{}/synonyms"

HEADERS = {
    "User-Agent": "GeoPharm/1.0"
}


def search_knapsack(scientific_name):
    """
    KNApSAcK에서 특정 학명으로 화합물 정보를 검색한다.
    """

    print()
    print("KNApSAcK search:", scientific_name)

    url = "https://www.knapsackfamily.com/knapsack_core/result.php"

    params = {
        "sname": "organism",
        "word": scientific_name
    }

    try:
        response = requests.get(
            url,
            params=params,
            headers=HEADERS,
            timeout=30
        )

        print("HTTP status:", response.status_code)

        if response.status_code != 200:
            return pd.DataFrame()

        soup = BeautifulSoup(response.text, "html.parser")

        tables = soup.find_all("table")

        print("Tables found:", len(tables))

        rows = []

        for table in tables:

            for tr in table.find_all("tr"):

                cells = tr.find_all(["th", "td"])

                if len(cells) < 6:
                    continue

                values = [
                    cell.get_text(" ", strip=True)
                    for cell in cells
                ]

                knapsack_id = values[0]

                if not knapsack_id.startswith("C"):
                    continue

                rows.append(
                    {
                        "Plant_ID": "EXTERNAL001",
                        "Scientific_Name": scientific_name,
                        "KNApSAcK_ID": knapsack_id,
                        "CAS": values[1],
                        "Compound_Name": values[2],
                        "Molecular_Formula": values[3],
                        "Molecular_Weight": values[4],
                        "KNApSAcK_Organism": values[5]
                    }
                )

        result_df = pd.DataFrame(rows)

        if len(result_df) > 0:
            result_df = result_df.drop_duplicates(
                subset=["KNApSAcK_ID"]
            )

        print("Compounds found:", len(result_df))

        return result_df

    except Exception as e:

        print("KNApSAcK search error:", e)

        return pd.DataFrame()


def get_gbif_synonyms(scientific_name):
    """
    GBIF에서 입력 학명의 동의명(synonym)을 자동으로 가져온다.
    """

    print()
    print("GBIF synonym search:", scientific_name)

    synonyms = []

    try:

        # --------------------------------------------------
        # 1. GBIF species match
        # --------------------------------------------------

        response = requests.get(
            GBIF_MATCH_URL,
            params={
                "name": scientific_name
            },
            headers=HEADERS,
            timeout=30
        )

        print("GBIF match HTTP:", response.status_code)

        if response.status_code != 200:
            return synonyms

        data = response.json()

        usage_key = data.get("usageKey")

        if not usage_key:
            print("GBIF usageKey not found")
            return synonyms

        print("GBIF usageKey:", usage_key)

        # --------------------------------------------------
        # 2. GBIF synonyms
        # --------------------------------------------------

        synonym_url = GBIF_SYNONYM_URL.format(usage_key)

        response = requests.get(
            synonym_url,
            headers=HEADERS,
            timeout=30
        )

        print("GBIF synonym HTTP:", response.status_code)

        if response.status_code != 200:
            return synonyms

        synonym_data = response.json()

        results = synonym_data.get("results", [])

        print("GBIF synonyms found:", len(results))

        for item in results:

            name = item.get("scientificName")

            if not name:
                name = item.get("canonicalName")

            if not name:
                continue

            # 저자명 제거를 위해 canonicalName을 우선 사용
            canonical_name = item.get("canonicalName")

            if canonical_name:
                name = canonical_name

            name = str(name).strip()

            if not name:
                continue

            if name.lower() == scientific_name.lower():
                continue

            if name not in synonyms:
                synonyms.append(name)

        return synonyms

    except Exception as e:

        print("GBIF synonym search error:", e)

        return synonyms


def build_search_names(scientific_name):
    """
    현재 학명 + GBIF 동의명을 검색 순서대로 만든다.
    """

    search_names = []

    scientific_name = scientific_name.strip()

    if scientific_name:
        search_names.append(scientific_name)

    synonyms = get_gbif_synonyms(scientific_name)

    for synonym in synonyms:

        if synonym.lower() == scientific_name.lower():
            continue

        if synonym not in search_names:
            search_names.append(synonym)

    return search_names


def search_knapsack_with_automatic_synonyms(scientific_name):
    """
    현재 학명을 먼저 검색하고,
    데이터가 없으면 GBIF 동의명을 자동으로 검색한다.
    """

    search_names = build_search_names(scientific_name)

    print()
    print("========================================")
    print("Automatic scientific-name search")
    print("========================================")

    print("Search names:", len(search_names))

    for index, name in enumerate(search_names, start=1):

        print(index, ".", name)

    print("========================================")

    for index, name in enumerate(search_names, start=1):

        print()
        print(
            "KNApSAcK search "
            + str(index)
            + "/"
            + str(len(search_names))
            + ": "
            + name
        )

        result_df = search_knapsack(name)

        if len(result_df) > 0:

            print()
            print("========================================")
            print("KNApSAcK compound data found")
            print("Search name:", name)
            print("Compound count:", len(result_df))
            print("========================================")

            # 프로그램에 등록된 현재 학명을 유지한다.
            result_df["Scientific_Name"] = scientific_name

            # 실제 KNApSAcK에서 데이터를 찾은 학명을 기록한다.
            result_df["KNApSAcK_Search_Name"] = name

            return result_df

    print()
    print("========================================")
    print("No KNApSAcK compound data found")
    print("========================================")

    return pd.DataFrame()


def main():

    print("========================================")
    print("GeoPharm External Plant Search")
    print("Automatic Scientific Synonym Search")
    print("========================================")

    scientific_name = input(
        "Scientific name: "
    ).strip()

    if not scientific_name:

        print("Scientific name is empty.")

        return

    result_df = search_knapsack_with_automatic_synonyms(
        scientific_name
    )

    if len(result_df) == 0:

        print()
        print("External plant search completed.")
        print("No compound data found.")

        return

    result_df.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8-sig"
    )

    print()
    print("========================================")
    print("External plant search completed")
    print("========================================")

    print("Plant:", scientific_name)

    print(
        "KNApSAcK search name:",
        result_df["KNApSAcK_Search_Name"].iloc[0]
    )

    print(
        "Compound count:",
        len(result_df)
    )

    print("Saved file:", OUTPUT_FILE)

    print()
    print("First 10 compounds:")

    print(
        result_df[
            [
                "KNApSAcK_ID",
                "Compound_Name",
                "Molecular_Formula",
                "Molecular_Weight"
            ]
        ].head(10).to_string(index=False)
    )


if __name__ == "__main__":
    main()