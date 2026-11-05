"""Stable compound identifiers when external database IDs are unavailable."""

import re

import pandas as pd


IDENTITY_COLUMNS = ("ChEMBL_ID", "InChIKey", "PubChem_CID", "KNApSAcK_ID", "Compound_Name")


def _clean(value):
    if pd.isna(value):
        return ""
    value = str(value).strip()
    if value.lower() in {"", "nan", "none", "null", "<na>"}:
        return ""
    return value


def compound_key(row):
    """Return the strongest available compound identity for a mapping or Series."""
    for column in IDENTITY_COLUMNS:
        value = _clean(row.get(column, ""))
        if not value:
            continue
        if column == "PubChem_CID":
            value = re.sub(r"\.0+$", "", value)
        if column == "Compound_Name":
            value = " ".join(value.casefold().split())
        else:
            value = value.upper()
        prefix = {"ChEMBL_ID": "CHEMBL", "InChIKey": "INCHIKEY", "PubChem_CID": "PUBCHEM", "KNApSAcK_ID": "KNAPSACK", "Compound_Name": "NAME"}[column]
        return f"{prefix}:{value}"
    return ""


def compound_keys(frame):
    """Vectorized-style row mapping, compatible with old and new CSV schemas."""
    if frame.empty:
        return pd.Series(index=frame.index, dtype="object")
    available = [column for column in IDENTITY_COLUMNS if column in frame.columns]
    if not available:
        return pd.Series([""] * len(frame), index=frame.index, dtype="object")
    return frame.apply(compound_key, axis=1).astype("object")
