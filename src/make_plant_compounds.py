import pandas as pd


plants = [
    {
        "Plant_ID": "PLANT001",
        "Common_Name_KO": "인삼",
        "English_Name": "Korean ginseng",
        "Scientific_Name": "Panax ginseng"
    },
    {
        "Plant_ID": "PLANT002",
        "Common_Name_KO": "당귀",
        "English_Name": "Korean angelica",
        "Scientific_Name": "Angelica gigas"
    },
    {
        "Plant_ID": "PLANT003",
        "Common_Name_KO": "황기",
        "English_Name": "Mongolian milkvetch",
        "Scientific_Name": "Astragalus mongholicus"
    },
    {
        "Plant_ID": "PLANT004",
        "Common_Name_KO": "감초",
        "English_Name": "Ural licorice",
        "Scientific_Name": "Glycyrrhiza uralensis"
    },
    {
        "Plant_ID": "PLANT005",
        "Common_Name_KO": "작약",
        "English_Name": "Chinese peony",
        "Scientific_Name": "Paeonia lactiflora"
    },
    {
        "Plant_ID": "PLANT006",
        "Common_Name_KO": "맥문동",
        "English_Name": "Mondo grass",
        "Scientific_Name": "Ophiopogon japonicus"
    },
    {
        "Plant_ID": "PLANT007",
        "Common_Name_KO": "오미자",
        "English_Name": "Chinese magnolia vine",
        "Scientific_Name": "Schisandra chinensis"
    },
    {
        "Plant_ID": "PLANT008",
        "Common_Name_KO": "구기자",
        "English_Name": "Chinese matrimony vine",
        "Scientific_Name": "Lycium chinense"
    },
    {
        "Plant_ID": "PLANT009",
        "Common_Name_KO": "지황",
        "English_Name": "Chinese foxglove",
        "Scientific_Name": "Rehmannia glutinosa"
    },
    {
        "Plant_ID": "PLANT010",
        "Common_Name_KO": "대추",
        "English_Name": "Chinese jujube",
        "Scientific_Name": "Ziziphus jujuba"
    },
    {
        "Plant_ID": "PLANT011",
        "Common_Name_KO": "황금",
        "English_Name": "Baikal skullcap",
        "Scientific_Name": "Scutellaria baicalensis"
    },
    {
        "Plant_ID": "PLANT012",
        "Common_Name_KO": "황련",
        "English_Name": "Chinese goldthread",
        "Scientific_Name": "Coptis chinensis"
    },
    {
        "Plant_ID": "PLANT013",
        "Common_Name_KO": "치자",
        "English_Name": "Cape jasmine",
        "Scientific_Name": "Gardenia jasminoides"
    },
    {
        "Plant_ID": "PLANT014",
        "Common_Name_KO": "산수유",
        "English_Name": "Japanese cornel",
        "Scientific_Name": "Cornus officinalis"
    },
    {
        "Plant_ID": "PLANT015",
        "Common_Name_KO": "두충",
        "English_Name": "Hardy rubber tree",
        "Scientific_Name": "Eucommia ulmoides"
    },
    {
        "Plant_ID": "PLANT016",
        "Common_Name_KO": "도라지",
        "English_Name": "Balloon flower",
        "Scientific_Name": "Platycodon grandiflorus"
    },
    {
        "Plant_ID": "PLANT017",
        "Common_Name_KO": "더덕",
        "English_Name": "Lanceolate bonnet bellflower",
        "Scientific_Name": "Codonopsis lanceolata"
    },
    {
        "Plant_ID": "PLANT018",
        "Common_Name_KO": "생강",
        "English_Name": "Ginger",
        "Scientific_Name": "Zingiber officinale"
    },
    {
        "Plant_ID": "PLANT019",
        "Common_Name_KO": "강황",
        "English_Name": "Turmeric",
        "Scientific_Name": "Curcuma longa"
    },
    {
        "Plant_ID": "PLANT020",
        "Common_Name_KO": "박하",
        "English_Name": "Mint",
        "Scientific_Name": "Mentha canadensis"
    },
    {
        "Plant_ID": "PLANT021",
        "Common_Name_KO": "목단",
        "English_Name": "Tree peony",
        "Scientific_Name": "Paeonia suffruticosa"
    },
    {
        "Plant_ID": "PLANT022",
        "Common_Name_KO": "오가피",
        "English_Name": "Siberian ginseng",
        "Scientific_Name": "Eleutherococcus sessiliflorus"
    },
    {
        "Plant_ID": "PLANT023",
        "Common_Name_KO": "백출",
        "English_Name": "Baizhu",
        "Scientific_Name": "Atractylodes macrocephala"
    },
    {
        "Plant_ID": "PLANT024",
        "Common_Name_KO": "오수유",
        "English_Name": "Evodia",
        "Scientific_Name": "Tetradium ruticarpum"
    },
    {
        "Plant_ID": "PLANT025",
        "Common_Name_KO": "택사",
        "English_Name": "Oriental water plantain",
        "Scientific_Name": "Alisma orientale"
    },
    {
        "Plant_ID": "PLANT026",
        "Common_Name_KO": "방풍",
        "English_Name": "Siler",
        "Scientific_Name": "Saposhnikovia divaricata"
    },
    {
        "Plant_ID": "PLANT027",
        "Common_Name_KO": "황정",
        "English_Name": "Siberian Solomon's seal",
        "Scientific_Name": "Polygonatum sibiricum"
    },
    {
        "Plant_ID": "PLANT028",
        "Common_Name_KO": "익모초",
        "English_Name": "Chinese motherwort",
        "Scientific_Name": "Leonurus japonicus"
    },
    {
        "Plant_ID": "PLANT029",
        "Common_Name_KO": "결명자",
        "English_Name": "Sicklepod",
        "Scientific_Name": "Senna tora"
    },
    {
        "Plant_ID": "PLANT030",
        "Common_Name_KO": "단삼",
        "English_Name": "Danshen",
        "Scientific_Name": "Salvia miltiorrhiza"
    }
]


df = pd.DataFrame(plants)


# 기본 검사
assert len(df) == 30
assert df["Plant_ID"].nunique() == 30
assert df["Scientific_Name"].nunique() == 30


df.to_csv(
    "data/raw/medicinal_plants.csv",
    index=False,
    encoding="utf-8-sig"
)


print("========================================")
print("약용식물 목록 생성 완료")
print("========================================")

print()
print("전체 식물:", len(df))
print("고유 Plant_ID:", df["Plant_ID"].nunique())
print("고유 학명:", df["Scientific_Name"].nunique())

print()
print(df.to_string(index=False))

print()
print("파일:")
print("data/raw/medicinal_plants.csv")