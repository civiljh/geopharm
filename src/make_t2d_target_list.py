import pandas as pd
from pathlib import Path


OUTPUT = Path("data/processed/t2d_target_list.csv")

targets = [
    {
        "Gene_Name": "DPP4",
        "UniProt_ID": "P27487",
        "Protein_Name": "Dipeptidyl peptidase 4",
        "Disease": "Type 2 diabetes mellitus",
        "Target_Evidence": "Strong",
        "Target_Role": "Established therapeutic target",
        "Evidence_Note": "DPP4 is a well-established therapeutic target in type 2 diabetes.",
    },
    {
        "Gene_Name": "FFAR1",
        "UniProt_ID": "O14842",
        "Protein_Name": "Free fatty acid receptor 1",
        "Disease": "Type 2 diabetes mellitus",
        "Target_Evidence": "Strong",
        "Target_Role": "Therapeutic target candidate",
        "Evidence_Note": "FFAR1 has been investigated as a therapeutic target for type 2 diabetes and insulin secretion.",
    },
    {
        "Gene_Name": "PPARG",
        "UniProt_ID": "P37231",
        "Protein_Name": "Peroxisome proliferator-activated receptor gamma",
        "Disease": "Type 2 diabetes mellitus",
        "Target_Evidence": "Strong",
        "Target_Role": "Established therapeutic target",
        "Evidence_Note": "PPAR-gamma is an established pharmacological target related to insulin sensitivity and type 2 diabetes.",
    },
    {
        "Gene_Name": "FTO",
        "UniProt_ID": "Q9C0B1",
        "Protein_Name": "Alpha-ketoglutarate-dependent dioxygenase FTO",
        "Disease": "Type 2 diabetes mellitus",
        "Target_Evidence": "Disease-associated",
        "Target_Role": "Disease-associated target",
        "Evidence_Note": "FTO has genetic and disease-association evidence related to type 2 diabetes, but it should not be treated as an established therapeutic target in this analysis.",
    },
    {
        "Gene_Name": "SLC22A1",
        "UniProt_ID": "O15245",
        "Protein_Name": "Solute carrier family 22 member 1",
        "Disease": "Type 2 diabetes mellitus",
        "Target_Evidence": "Contextual",
        "Target_Role": "Transporter-related candidate",
        "Evidence_Note": "SLC22A1 is included as a diabetes-relevant transporter candidate for exploratory screening, not as a confirmed therapeutic target.",
    },
    {
        "Gene_Name": "SLC22A2",
        "UniProt_ID": "O15244",
        "Protein_Name": "Solute carrier family 22 member 2",
        "Disease": "Type 2 diabetes mellitus",
        "Target_Evidence": "Contextual",
        "Target_Role": "Transporter-related candidate",
        "Evidence_Note": "SLC22A2 is included as a diabetes-relevant transporter candidate for exploratory screening, not as a confirmed therapeutic target.",
    },
]

df = pd.DataFrame(targets)

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
df.to_csv(OUTPUT, index=False, encoding="utf-8-sig")

print("T2D target list created.")
print("File:", OUTPUT)
print("Targets:", len(df))
print()
print(df.to_string(index=False))