"""Generate plant-compound predictions for newly registered disease targets."""

import json
import os
import sys
import tempfile
import time
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import joblib
import numpy as np
import pandas as pd

try:
    from src.compound_identity import compound_keys
except ImportError:
    from compound_identity import compound_keys


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "processed"
PREDICTION_FILE = DATA / "plant_ai_human_predictions.csv"
PREDICTION_READY_FILE = DATA / "plant_ai_prediction_ready.csv"
NEW_PLANT_PREDICTION_READY_FILE = DATA / "new_plant_ai_prediction_ready.csv"
EXTERNAL_PLANT_PREDICTION_READY_FILE = DATA / "external_plant_ai_prediction_ready.csv"
RDKIT_FILE = DATA / "rdkit_features.csv"
PROTEIN_FEATURE_FILE = DATA / "protein_features.csv"
SEQUENCE_FILE = DATA / "ml_uniprot_sequences.csv"
TARGET_FILE = DATA / "human_target_list.csv"
PLANT_FILE = ROOT / "data" / "raw" / "medicinal_plants.csv"
MODEL_FILE = DATA / "random_forest_ic50_protein.joblib"
LOCK_FILE = DATA / ".disease_prediction.lock"
PREDICTION_BATCH_SIZE = 256
_LOCK_DESCRIPTOR = None

AMINO_ACIDS = "ACDEFGHIKLMNPQRSTVWY"
AMINO_GROUPS = {
    "Hydrophobic_Fraction": "AILMFWVY",
    "Aromatic_Fraction": "FWY",
    "Positive_Fraction": "KR",
    "Negative_Fraction": "DE",
    "Polar_Fraction": "STNQ",
}
OUTPUT_COLUMNS = [
    "Plant_ID", "KNApSAcK_ID", "Compound_Name", "ChEMBL_ID", "InChIKey", "PubChem_CID", "Compound_Key", "UniProt_ID",
    "Predicted_pChEMBL", "Common_Name_KO", "English_Name", "Scientific_Name",
    "Protein_Name", "Gene_Name", "Organism", "Reviewed", "Prediction_Source",
]


def read_csv(path):
    return pd.read_csv(path, low_memory=False) if path.exists() else pd.DataFrame()


def clean_text(value):
    if pd.isna(value):
        return ""
    return str(value).strip()


def acquire_lock(timeout=1800):
    """Serialize prediction writers with an OS lock that is released on process exit."""
    global _LOCK_DESCRIPTOR
    if _LOCK_DESCRIPTOR is not None:
        raise RuntimeError("This process already holds the disease prediction lock.")
    LOCK_FILE.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(str(LOCK_FILE), os.O_CREAT | os.O_RDWR)
    if os.name == "nt":
        import msvcrt

        if os.fstat(descriptor).st_size == 0:
            os.write(descriptor, b"\0")
    else:
        import fcntl

    deadline = time.monotonic() + timeout
    while True:
        try:
            if os.name == "nt":
                os.lseek(descriptor, 0, os.SEEK_SET)
                msvcrt.locking(descriptor, msvcrt.LK_NBLCK, 1)
            else:
                fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
            os.ftruncate(descriptor, 0)
            os.lseek(descriptor, 0, os.SEEK_SET)
            os.write(descriptor, str(os.getpid()).encode("ascii"))
            _LOCK_DESCRIPTOR = descriptor
            return
        except (BlockingIOError, OSError):
            if time.monotonic() >= deadline:
                os.close(descriptor)
                raise TimeoutError("Another disease prediction job is still running.")
            time.sleep(0.25)


def release_lock():
    global _LOCK_DESCRIPTOR
    if _LOCK_DESCRIPTOR is None:
        return
    descriptor = _LOCK_DESCRIPTOR
    _LOCK_DESCRIPTOR = None
    try:
        if os.name == "nt":
            import msvcrt

            os.lseek(descriptor, 0, os.SEEK_SET)
            msvcrt.locking(descriptor, msvcrt.LK_UNLCK, 1)
        else:
            import fcntl

            fcntl.flock(descriptor, fcntl.LOCK_UN)
    finally:
        os.close(descriptor)


def atomic_write_csv(frame, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temp_name = tempfile.mkstemp(prefix=path.stem + "_", suffix=".tmp", dir=path.parent)
    os.close(handle)
    try:
        frame.to_csv(temp_name, index=False, encoding="utf-8-sig")
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def fetch_uniprot_by_gene(gene):
    query = f"gene_exact:{gene} AND organism_id:9606"
    params = urlencode({
        "query": query,
        "format": "json",
        "fields": "accession,protein_name,gene_primary,reviewed,sequence",
        "size": 10,
    })
    request = Request(
        f"https://rest.uniprot.org/uniprotkb/search?{params}",
        headers={"User-Agent": "GeoPharm/1.0", "Accept": "application/json"},
    )
    with urlopen(request, timeout=20) as response:
        entries = json.loads(response.read().decode("utf-8")).get("results", [])
    entries = [entry for entry in entries if entry.get("primaryAccession") and (entry.get("sequence") or {}).get("value")]
    entries.sort(key=lambda entry: (not bool(entry.get("entryType", "").startswith("UniProtKB reviewed")), entry["primaryAccession"]))
    return entries[0] if entries else None


def fetch_uniprot_by_accession(accession):
    request = Request(
        f"https://rest.uniprot.org/uniprotkb/{accession}.json",
        headers={"User-Agent": "GeoPharm/1.0", "Accept": "application/json"},
    )
    with urlopen(request, timeout=20) as response:
        entry = json.loads(response.read().decode("utf-8"))
    if (entry.get("organism") or {}).get("taxonId") != 9606:
        return None
    sequence = (entry.get("sequence") or {}).get("value", "")
    if not sequence:
        return None
    return {
        "primaryAccession": entry.get("primaryAccession", accession),
        "proteinDescription": entry.get("proteinDescription", {}),
        "entryType": entry.get("entryType", ""),
        "sequence": {"value": sequence},
    }


def entry_details(entry):
    description = entry.get("proteinDescription") or {}
    protein_name = (
        (description.get("recommendedName") or {}).get("fullName") or
        (description.get("submissionNames") or [{}])[0].get("fullName") or {}
    )
    if isinstance(protein_name, dict):
        protein_name = protein_name.get("value", "")
    return str(protein_name or ""), str((entry.get("sequence") or {}).get("value", "")).upper()


def make_protein_features(sequence, accession):
    sequence = str(sequence).upper().strip()
    length = len(sequence)
    if not length or not any(char in AMINO_ACIDS for char in sequence):
        raise ValueError("The protein sequence is empty or contains no recognized amino acids.")
    row = {"UniProt_ID": accession, "Sequence_Length": length}
    row.update({f"AA_{aa}": sequence.count(aa) / length for aa in AMINO_ACIDS})
    row.update({name: sum(sequence.count(aa) for aa in group) / length for name, group in AMINO_GROUPS.items()})
    return row


def resolve_targets(targets):
    sequences = read_csv(SEQUENCE_FILE)
    sequence_by_id = {}
    gene_to_id = {}
    details_by_id = {}
    reviewed_by_id = {}
    if not sequences.empty:
        for _, row in sequences.iterrows():
            accession = clean_text(row.get("UniProt_ID", ""))
            if not accession:
                continue
            sequence_by_id[accession] = clean_text(row.get("Sequence", ""))
            gene = clean_text(row.get("Gene_Name", "")).upper()
            if gene:
                gene_to_id.setdefault(gene, accession)
            details_by_id[accession] = clean_text(row.get("Protein_Name", ""))
            reviewed_by_id[accession] = str(row.get("Reviewed", "")).strip().lower() in {"true", "1"}
    for path in (TARGET_FILE, PREDICTION_FILE):
        table = read_csv(path)
        if table.empty or not {"Gene_Name", "UniProt_ID"}.issubset(table.columns):
            continue
        for _, row in table[["Gene_Name", "UniProt_ID"]].dropna().iterrows():
            gene, accession = clean_text(row["Gene_Name"]).upper(), clean_text(row["UniProt_ID"])
            if gene and accession:
                gene_to_id.setdefault(gene, accession)

    resolved, statuses = [], []
    resolved_ids = set()
    for target in targets:
        target = dict(target)
        gene = clean_text(target.get("gene_symbol") or target.get("Gene_Name") or "").upper()
        accession = clean_text(target.get("uniprot_id") or target.get("UniProt_ID") or "")
        entry = None
        try:
            if not accession and gene:
                accession = gene_to_id.get(gene, "")
            if accession and accession in sequence_by_id:
                sequence = sequence_by_id[accession]
                protein_name = details_by_id.get(accession, str(target.get("protein_name") or ""))
                reviewed = reviewed_by_id.get(accession, False)
            else:
                entry = fetch_uniprot_by_accession(accession) if accession else fetch_uniprot_by_gene(gene)
                if not entry and gene:
                    entry = fetch_uniprot_by_gene(gene)
                if not entry:
                    raise ValueError("No human UniProt entry with a protein sequence was found.")
                accession = str(entry.get("primaryAccession", "")).strip()
                protein_name, sequence = entry_details(entry)
                reviewed = str(entry.get("entryType", "")).startswith("UniProtKB reviewed")
            features = make_protein_features(sequence, accession)
            if accession in resolved_ids:
                statuses.append({"gene_symbol": gene or accession, "uniprot_id": accession, "status": "duplicate_target"})
                continue
            resolved_ids.add(accession)
            target.update({"uniprot_id": accession, "protein_name": target.get("protein_name") or protein_name, "gene_symbol": gene})
            resolved.append({"target": target, "features": features, "reviewed": reviewed})
            statuses.append({"gene_symbol": gene or accession, "uniprot_id": accession, "protein_name": target.get("protein_name", ""), "status": "resolved"})
        except Exception as error:
            statuses.append({"gene_symbol": gene or accession or "Unknown target", "uniprot_id": accession, "status": "unavailable", "message": str(error)[:240]})
    return resolved, statuses


def generate_predictions(targets, plant_id=None, source="new", refresh=False):
    resolved, statuses = resolve_targets(targets)
    if not resolved:
        return {"targets": statuses, "generated_rows": 0, "status": "no_targets_resolved"}
    if plant_id:
        source_files = {
            "new": NEW_PLANT_PREDICTION_READY_FILE,
            "external": EXTERNAL_PLANT_PREDICTION_READY_FILE,
        }
        if source not in source_files:
            raise ValueError("Unsupported plant prediction source.")
        input_file = source_files[source]
        required_files = (input_file, MODEL_FILE, PROTEIN_FEATURE_FILE)
    else:
        input_file = PREDICTION_READY_FILE
        required_files = (input_file, RDKIT_FILE, MODEL_FILE, PROTEIN_FEATURE_FILE)
    missing_files = [str(path.relative_to(ROOT)) for path in required_files if not path.exists()]
    if missing_files:
        for status in statuses:
            if status["status"] == "resolved":
                status.update(status="unavailable", message="Prediction resources are missing: " + ", ".join(missing_files))
        return {"targets": statuses, "generated_rows": 0, "status": "resources_unavailable"}

    acquire_lock()
    try:
        plant_rows = read_csv(input_file)
        rdkit = read_csv(RDKIT_FILE) if not plant_id else pd.DataFrame()
        existing = read_csv(PREDICTION_FILE)
        metadata = read_csv(PLANT_FILE)
        model = joblib.load(MODEL_FILE)
        morgan_columns = [column for column in plant_rows.columns if column.startswith("Morgan_")] if plant_id else [column for column in rdkit.columns if column.startswith("Morgan_")]
        protein_columns = [column for column in read_csv(PROTEIN_FEATURE_FILE).columns if column != "UniProt_ID"]
        model_columns = list(getattr(model, "feature_names_in_", []))
        if not morgan_columns or not protein_columns or model_columns != morgan_columns + protein_columns:
            raise ValueError("The local prediction feature schema does not match the trained model.")
        if plant_rows.empty or (not plant_id and rdkit.empty):
            raise ValueError("Plant compounds or Morgan fingerprints are unavailable.")
        if plant_id:
            plant_rows = plant_rows[plant_rows["Plant_ID"].astype(str) == str(plant_id)].copy()
            if plant_rows.empty:
                raise ValueError("The newly registered plant has no prepared compound features.")
        else:
            plant_rows = plant_rows.merge(rdkit[["ChEMBL_ID"] + morgan_columns], on="ChEMBL_ID", how="inner", validate="many_to_one")
        plant_rows["Compound_Key"] = compound_keys(plant_rows)
        plant_rows = plant_rows[plant_rows["Compound_Key"] != ""].copy()
        plant_rows = plant_rows.drop_duplicates(["Plant_ID", "Compound_Key"]).reset_index(drop=True)
        if plant_rows.empty:
            raise ValueError("No plant compounds with a usable compound identifier are available for prediction.")
        if metadata.empty or "Plant_ID" not in metadata.columns:
            metadata = pd.DataFrame(columns=["Plant_ID", "Common_Name_KO", "English_Name", "Scientific_Name"])
        metadata_columns = [column for column in ("Plant_ID", "Common_Name_KO", "English_Name", "Scientific_Name") if column in metadata.columns]
        plant_rows = plant_rows.merge(metadata[metadata_columns].drop_duplicates("Plant_ID"), on="Plant_ID", how="left", suffixes=("", "_metadata"))
        for column in ("Common_Name_KO", "English_Name", "Scientific_Name"):
            if column not in plant_rows.columns:
                plant_rows[column] = ""
            elif column + "_metadata" in plant_rows.columns:
                plant_rows[column] = plant_rows[column].replace("", pd.NA).fillna(plant_rows[column + "_metadata"])
                plant_rows = plant_rows.drop(columns=[column + "_metadata"])

        existing_keys = set()
        if not existing.empty and {"Plant_ID", "UniProt_ID"}.issubset(existing.columns):
            existing["Compound_Key"] = compound_keys(existing)
            existing_keys = set(zip(existing["Plant_ID"].astype(str), existing["Compound_Key"].astype(str), existing["UniProt_ID"].astype(str)))
        output = []
        for resolved_target in resolved:
            target = resolved_target["target"]
            accession = target["uniprot_id"]
            protein_values = resolved_target["features"]
            target_keys = pd.Series(
                list(zip(plant_rows["Plant_ID"].astype(str), plant_rows["Compound_Key"].astype(str), [accession] * len(plant_rows))),
                index=plant_rows.index,
            )
            pending_mask = pd.Series(True, index=plant_rows.index) if refresh else ~target_keys.isin(existing_keys)
            pending = plant_rows.loc[pending_mask].reset_index(drop=True)
            if pending.empty:
                for status in statuses:
                    if status.get("uniprot_id") == accession and status["status"] == "resolved":
                        status.update(status="already_available", generated_rows=0)
                continue
            feature_row = pd.DataFrame([{column: protein_values[column] for column in protein_columns}])
            predictions = []
            feature_columns = morgan_columns + protein_columns
            try:
                for start in range(0, len(pending), PREDICTION_BATCH_SIZE):
                    batch = pending.iloc[start:start + PREDICTION_BATCH_SIZE]
                    matrix = pd.concat(
                        [batch[morgan_columns].reset_index(drop=True), pd.concat([feature_row] * len(batch), ignore_index=True)],
                        axis=1,
                    )
                    matrix = matrix.reindex(columns=feature_columns)
                    predictions.extend(model.predict(matrix).tolist())
            except Exception as error:
                for status in statuses:
                    if status.get("uniprot_id") == accession and status["status"] == "resolved":
                        status.update(status="unavailable", message=("Prediction failed: " + str(error))[:240])
                continue
            for (_, row), predicted in zip(pending.iterrows(), predictions):
                output.append({
                    "Plant_ID": row.get("Plant_ID", ""),
                    "KNApSAcK_ID": row.get("KNApSAcK_ID", ""),
                    "Compound_Name": row.get("Compound_Name", ""),
                    "ChEMBL_ID": row.get("ChEMBL_ID", ""),
                    "InChIKey": row.get("InChIKey", ""),
                    "PubChem_CID": row.get("PubChem_CID", ""),
                    "Compound_Key": row.get("Compound_Key", ""),
                    "UniProt_ID": accession,
                    "Predicted_pChEMBL": float(predicted),
                    "Common_Name_KO": row.get("Common_Name_KO", ""),
                    "English_Name": row.get("English_Name", ""),
                    "Scientific_Name": row.get("Scientific_Name", ""),
                    "Protein_Name": target.get("protein_name", ""),
                    "Gene_Name": target.get("gene_symbol", ""),
                    "Organism": "Homo sapiens",
                    "Reviewed": resolved_target["reviewed"],
                    "Prediction_Source": "AI model extrapolation",
                })
            for status in statuses:
                if status.get("uniprot_id") == accession and status["status"] == "resolved":
                    status.update(status="generated", generated_rows=len(pending))

        if output:
            additions = pd.DataFrame(output).reindex(columns=OUTPUT_COLUMNS)
            successful_target_ids = set(additions["UniProt_ID"].astype(str))
            if refresh and not existing.empty:
                replace_mask = (
                    existing["Plant_ID"].astype(str).isin(set(plant_rows["Plant_ID"].astype(str)))
                    & existing["UniProt_ID"].astype(str).isin(successful_target_ids)
                )
                existing = existing.loc[~replace_mask].copy()
            combined = pd.concat([existing.reindex(columns=list(dict.fromkeys(list(existing.columns) + OUTPUT_COLUMNS))), additions], ignore_index=True)
            combined["Compound_Key"] = compound_keys(combined)
            combined = combined.drop_duplicates(["Plant_ID", "Compound_Key", "UniProt_ID"], keep="last")
            atomic_write_csv(combined, PREDICTION_FILE)
        return {
            "targets": statuses,
            "generated_rows": len(output),
            "status": "complete" if all(item["status"] not in {"unavailable"} for item in statuses) else "partial",
        }
    finally:
        release_lock()


def main():
    try:
        payload = json.load(sys.stdin)
        result = generate_predictions(
            payload.get("targets") or [],
            plant_id=payload.get("plant_id"),
            source=payload.get("source", "new"),
            refresh=bool(payload.get("refresh", False)),
        )
        print(json.dumps(result, ensure_ascii=False))
    except Exception as error:
        print(json.dumps({"status": "failed", "generated_rows": 0, "targets": [], "error": str(error)[:500]}, ensure_ascii=False))
        sys.exit(1)


if __name__ == "__main__":
    main()
