import requests
import pandas as pd

uniprot_id = "P00533"

url = f"https://rest.uniprot.org/uniprotkb/{uniprot_id}.json"

response = requests.get(url)

print("HTTP 상태 코드:", response.status_code)
response.raise_for_status()

data = response.json()

primary_accession = data.get("primaryAccession")
uniprot_name = data.get("uniProtkbId")

organism = data.get("organism", {})
scientific_name = organism.get("scientificName")

protein_description = data.get("proteinDescription", {})
recommended_name = protein_description.get("recommendedName", {})
full_name = recommended_name.get("fullName", {})
protein_name = full_name.get("value")

genes = data.get("genes", [])

if genes:
    gene_name = genes[0].get("geneName", {}).get("value")
else:
    gene_name = None

result = {
    "UniProt_ID": primary_accession,
    "UniProt_Name": uniprot_name,
    "Protein_Name": protein_name,
    "Gene_Name": gene_name,
    "Organism": scientific_name
}

df = pd.DataFrame([result])

print(df)

df.to_csv(
    "data/raw/uniprot_test.csv",
    index=False,
    encoding="utf-8-sig"
)

print("UniProt CSV 저장 완료")