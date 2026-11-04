import pandas as pd
import os


# ============================================================
# GeoPharm
# External Plant Compound ??Plant_ID ?곌껐
#
# ??븷:
# 1. ?몃? ?뷀빀臾??곗씠???쎄린
# 2. Scientific_Name?쇰줈 ?앸Ъ DB 寃??
# 3. Plant_ID ?먮룞 ?곌껐
# 4. ?덈줈???뚯씪濡????
#
# 湲곗〈 external_plant_compounds.csv???섏젙?섏? ?딆뒿?덈떎.
# ============================================================


PLANT_FILE = "data/raw/medicinal_plants.csv"
EXTERNAL_FILE = "data/raw/external_plant_compounds.csv"
OUTPUT_FILE = "data/raw/external_plant_compounds_linked.csv"


# ------------------------------------------------------------
# ?뚯씪 ?뺤씤
# ------------------------------------------------------------

if not os.path.exists(PLANT_FILE):
    print("ERROR: ?앸Ъ DB ?뚯씪??李얠쓣 ???놁뒿?덈떎.")
    print(PLANT_FILE)
    raise SystemExit

if not os.path.exists(EXTERNAL_FILE):
    print("ERROR: ?몃? ?뷀빀臾??뚯씪??李얠쓣 ???놁뒿?덈떎.")
    print(EXTERNAL_FILE)
    raise SystemExit


# ------------------------------------------------------------
# ?곗씠???쎄린
# ------------------------------------------------------------

plants = pd.read_csv(
    PLANT_FILE,
    encoding="utf-8-sig"
)

compounds = pd.read_csv(
    EXTERNAL_FILE,
    encoding="utf-8-sig"
)


# ------------------------------------------------------------
# ?숇챸 ?뺣━
# ------------------------------------------------------------

plants["_Scientific_Key"] = (
    plants["Scientific_Name"]
    .astype(str)
    .str.strip()
    .str.lower()
)

compounds["_Scientific_Key"] = (
    compounds["Scientific_Name"]
    .astype(str)
    .str.strip()
    .str.lower()
)


# ------------------------------------------------------------
# Scientific_Name ??Plant_ID ?곌껐
# ------------------------------------------------------------

plant_id_map = (
    plants[
        [
            "_Scientific_Key",
            "Plant_ID",
            "Common_Name_KO",
            "English_Name",
            "Scientific_Name"
        ]
    ]
    .drop_duplicates(
        subset=["_Scientific_Key"]
    )
)


linked = compounds.merge(
    plant_id_map,
    on="_Scientific_Key",
    how="left",
    suffixes=("", "_DB")
)


# ------------------------------------------------------------
# ?곌껐 ?곹깭 ?뺤씤
# ------------------------------------------------------------

# 기존 DB에 존재하는 식물은 실제 Plant_ID로 자동 연결
linked["Plant_ID"] = linked["Plant_ID_DB"].where(linked["Plant_ID_DB"].notna(), linked["Plant_ID"])

linked_count = linked["Plant_ID_DB"].notna().sum()
unlinked_count = linked["Plant_ID_DB"].isna().sum()

print()
print("=" * 60)
print("External plant ??Plant_ID ?곌껐 寃곌낵")
print("=" * 60)

print()
print("?꾩껜 ?뷀빀臾?", len(linked))
print("?곌껐 ?깃났:", linked_count)
print("?곌껐 ?ㅽ뙣:", unlinked_count)


# ------------------------------------------------------------
# ?곌껐 ?ㅽ뙣 ?곗씠???뺤씤
# ------------------------------------------------------------

if unlinked_count > 0:

    print()
    print("=" * 60)
    print("?곌껐?섏? ?딆? ?앸Ъ")
    print("=" * 60)

    print(
        linked.loc[
            linked["Plant_ID"].isna(),
            ["Scientific_Name"]
        ]
        .drop_duplicates()
        .to_string(index=False)
    )


# ------------------------------------------------------------
# ?꾩떆 而щ읆 ?쒓굅
# ------------------------------------------------------------

linked = linked.drop(
    columns=["_Scientific_Key"]
)


# ------------------------------------------------------------
# ???
# ------------------------------------------------------------

linked.to_csv(
    OUTPUT_FILE,
    index=False,
    encoding="utf-8-sig"
)


# ------------------------------------------------------------
# 寃곌낵 ?뺤씤
# ------------------------------------------------------------

print()
print("=" * 60)
print("????꾨즺")
print("=" * 60)

print("?뚯씪:", OUTPUT_FILE)

print()
print("?앸Ъ蹂??뷀빀臾???")

summary = (
    linked
    .groupby(
        [
            "Plant_ID",
            "Common_Name_KO",
            "Scientific_Name_DB"
        ],
        dropna=False
    )
    .size()
    .reset_index(
        name="Compound_Count"
    )
)

print(
    summary.to_string(index=False)
)

print()
print("?꾨즺.")


