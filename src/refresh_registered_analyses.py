"""Refresh human predictions and derived analyses for current registered diseases."""

import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.disease_prediction_pipeline import generate_predictions


DATA = ROOT / "data" / "processed"
BACKUP_DIR = ROOT / "backups" / ("registered_analysis_refresh_" + datetime.now().strftime("%Y%m%d_%H%M%S"))
CATALOG_FILE = DATA / "disease_catalog.csv"
T2D_TARGET_FILE = DATA / "t2d_target_list.csv"
MODEL_TARGET_FILE = DATA / "human_target_list.csv"
PLANT_FILE = ROOT / "data" / "raw" / "medicinal_plants.csv"
GENERIC_PREDICTION_FILE = DATA / "plant_ai_predictions.csv"
HUMAN_PREDICTION_FILE = DATA / "plant_ai_human_predictions.csv"

T2D_REFRESH_SCRIPTS = [
    "make_t2d_predictions.py",
    "score_t2d_plants.py",
    "analyze_t2d_plant.py",
    "make_t2d_target_summary.py",
    "make_t2d_key_candidates.py",
    "make_t2d_analysis_data.py",
    "make_t2d_web_data.py",
]

BACKUP_FILES = [
    CATALOG_FILE,
    HUMAN_PREDICTION_FILE,
    DATA / "t2d_plant_predictions.csv",
    DATA / "t2d_plant_priority_score.csv",
    DATA / "t2d_plant_summary.csv",
    DATA / "t2d_plant_specific_predictions.csv",
    DATA / "t2d_top_candidates.csv",
    DATA / "t2d_target_summary.csv",
    DATA / "t2d_key_candidates.csv",
    DATA / "t2d_analysis_data.csv",
    DATA / "t2d_web_data.csv",
    DATA / "t2d_web_plants.csv",
    DATA / "t2d_web_targets.csv",
    DATA / "t2d_web_candidates.csv",
]


def read_csv(path):
    return pd.read_csv(path, encoding="utf-8-sig", low_memory=False)


def cell_text(value):
    if pd.isna(value):
        return ""
    return str(value).strip()


def atomic_write_csv(frame, path):
    descriptor, temp_name = tempfile.mkstemp(prefix="refresh_", suffix=".tmp", dir=path.parent)
    os.close(descriptor)
    try:
        frame.to_csv(temp_name, index=False, encoding="utf-8-sig")
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.remove(temp_name)


def backup_current_data():
    BACKUP_DIR.mkdir(parents=True, exist_ok=False)
    for path in BACKUP_FILES:
        if path.exists():
            shutil.copy2(path, BACKUP_DIR / path.name)
    return BACKUP_DIR


def collect_targets():
    catalog = read_csv(CATALOG_FILE)
    t2d_targets = read_csv(T2D_TARGET_FILE)
    frames = []
    if not catalog.empty:
        frames.append(catalog)
    if not t2d_targets.empty:
        frames.append(t2d_targets)
    if not frames:
        return []

    combined = pd.concat(frames, ignore_index=True, sort=False)
    targets = {}
    for _, row in combined.iterrows():
        gene = cell_text(row.get("Gene_Name")).upper()
        accession = cell_text(row.get("UniProt_ID"))
        key = accession.upper() or gene
        if not key:
            continue
        targets.setdefault(key, {
            "gene_symbol": gene,
            "uniprot_id": accession,
            "protein_name": cell_text(row.get("Protein_Name")),
        })
    return list(targets.values())


def rebuild_registered_human_predictions(target_ids):
    """Refresh disease-relevant predictions for all plants already in the generic output."""
    generic = read_csv(GENERIC_PREDICTION_FILE)
    model_targets = read_csv(MODEL_TARGET_FILE)
    plant_metadata = read_csv(PLANT_FILE)
    previous = read_csv(HUMAN_PREDICTION_FILE) if HUMAN_PREDICTION_FILE.exists() else pd.DataFrame()

    generic_ids = set(model_targets["UniProt_ID"].dropna().astype(str).str.strip())
    selected_ids = set(target_ids) & generic_ids
    generic = generic[generic["UniProt_ID"].fillna("").astype(str).str.strip().isin(selected_ids)].copy()
    generic = generic.merge(model_targets, on="UniProt_ID", how="left", validate="many_to_one")

    metadata_columns = [column for column in ("Plant_ID", "Common_Name_KO", "English_Name", "Scientific_Name") if column in plant_metadata.columns]
    generic = generic.merge(
        plant_metadata[metadata_columns].drop_duplicates("Plant_ID"),
        on="Plant_ID",
        how="left",
        suffixes=("", "_plant"),
    )
    for column in ("Common_Name_KO", "English_Name", "Scientific_Name"):
        plant_column = column + "_plant"
        if column not in generic.columns:
            generic[column] = ""
        if plant_column in generic.columns:
            generic[column] = generic[column].replace("", pd.NA).fillna(generic[plant_column])
            generic = generic.drop(columns=[plant_column])
    generic["Prediction_Source"] = "Existing trained-model prediction"

    # Keep disease-target predictions outside the 382-target baseline so they can be refreshed below.
    extra = pd.DataFrame()
    if not previous.empty and "UniProt_ID" in previous.columns:
        extra_ids = set(target_ids) - generic_ids
        extra = previous[previous["UniProt_ID"].fillna("").astype(str).str.strip().isin(extra_ids)].copy()

    columns = [
        "Plant_ID", "KNApSAcK_ID", "Compound_Name", "ChEMBL_ID", "UniProt_ID",
        "Predicted_pChEMBL", "Common_Name_KO", "English_Name", "Scientific_Name",
        "Protein_Name", "Gene_Name", "Organism", "Reviewed", "Prediction_Source",
    ]
    for frame in (generic, extra):
        for column in columns:
            if column not in frame.columns:
                frame[column] = ""
    combined = pd.concat([generic[columns], extra[columns]], ignore_index=True)
    combined = combined.drop_duplicates(["Plant_ID", "ChEMBL_ID", "UniProt_ID"], keep="last")
    atomic_write_csv(combined, HUMAN_PREDICTION_FILE)
    return len(combined), generic["Plant_ID"].nunique(), len(extra)


def refresh_catalog_status(results):
    catalog = read_csv(CATALOG_FILE)
    states = {}
    for result in results:
        for item in result.get("targets", []):
            keys = (
                str(item.get("gene_symbol", "")).strip().upper(),
                str(item.get("uniprot_id", "")).strip().upper(),
            )
            for key in keys:
                if not key:
                    continue
                state = states.setdefault(key, {"status": item.get("status", "unknown"), "rows": 0, "id": "", "protein": ""})
                if item.get("status") in {"generated", "already_available"}:
                    state["status"] = "Generated"
                elif state["status"] not in {"Generated", "Unavailable"}:
                    state["status"] = str(item.get("status", "unknown")).replace("_", " ").title()
                state["rows"] += int(item.get("generated_rows", 0) or 0)
                state["id"] = item.get("uniprot_id") or state["id"]
                state["protein"] = item.get("protein_name") or state["protein"]

    for column in ("Prediction_Status", "Prediction_Rows"):
        if column not in catalog.columns:
            catalog[column] = ""
    for index, row in catalog.iterrows():
        gene = cell_text(row.get("Gene_Name")).upper()
        accession = cell_text(row.get("UniProt_ID")).upper()
        state = states.get(accession) or states.get(gene)
        if not state:
            catalog.at[index, "Prediction_Status"] = "Unavailable"
            catalog.at[index, "Prediction_Rows"] = 0
            continue
        if state["id"]:
            catalog.at[index, "UniProt_ID"] = state["id"]
        if state["protein"]:
            catalog.at[index, "Protein_Name"] = state["protein"]
        catalog.at[index, "Prediction_Status"] = state["status"]
        catalog.at[index, "Prediction_Rows"] = state["rows"]
    atomic_write_csv(catalog, CATALOG_FILE)


def run_t2d_refresh():
    for script in T2D_REFRESH_SCRIPTS:
        print(f"Running T2D refresh step: {script}", flush=True)
        subprocess.run([sys.executable, str(ROOT / "src" / script)], cwd=ROOT, check=True)


def main():
    backup = backup_current_data()
    print(f"Backup created: {backup.relative_to(ROOT)}", flush=True)

    targets = collect_targets()
    model_targets = read_csv(MODEL_TARGET_FILE)
    target_ids = {str(target["uniprot_id"]).strip() for target in targets if target.get("uniprot_id")}
    rebuilt_rows, generic_plants, preserved_extra_rows = rebuild_registered_human_predictions(target_ids)
    print(
        f"Rebuilt disease prediction table with {rebuilt_rows:,} rows from {generic_plants} plants "
        f"and preserved {preserved_extra_rows:,} supplemental rows.",
        flush=True,
    )

    results = []
    for plant_id, source in ((None, "new"), ("PLANT046", "new"), ("PLANT032", "external")):
        result = generate_predictions(targets, plant_id=plant_id, source=source, refresh=True)
        results.append(result)
        label = "all main feature-ready plants" if plant_id is None else plant_id
        print(
            f"Disease predictions for {label}: status={result.get('status')}, "
            f"rows={result.get('generated_rows', 0):,}, "
            f"unavailable_targets={sum(item.get('status') == 'unavailable' for item in result.get('targets', []))}",
            flush=True,
        )
    refresh_catalog_status(results)

    run_t2d_refresh()
    print("Registered disease and T2D analyses refreshed.", flush=True)
    print(f"Safety backup: {backup.relative_to(ROOT)}", flush=True)


if __name__ == "__main__":
    main()
