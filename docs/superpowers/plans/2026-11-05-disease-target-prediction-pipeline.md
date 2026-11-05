# Disease Target Prediction Pipeline Implementation Plan

## 1. Build a reusable prediction service

- Add a module that resolves gene symbols to canonical human UniProt accessions and sequences, preferring local data and then using UniProt REST.
- Derive the trained model's protein feature schema from retrieved sequences.
- Load the existing compound fingerprints, model, and plant-compound rows; predict in bounded batches.
- Reuse existing predictions, deduplicate by compound and UniProt accession, and atomically persist compatible records.

## 2. Integrate disease registration

- Enrich saved disease targets with resolved UniProt IDs.
- Run the pipeline synchronously for the registered disease's targets after saving the disease.
- Return per-target counts/status and an English user-facing summary, preserving successful outputs when some targets cannot be resolved.
- Keep the endpoint capped at the existing 20 targets and avoid concurrent writes corrupting the prediction CSV.

## 3. Reflect pipeline outcomes in the website

- Update the registration interaction to show English progress and per-target outcomes while the request runs.
- Redirect to the disease analysis after completion and refresh prediction data so generated plants are visible.
- Label generated results as model predictions with extrapolation status where shown.

## 4. Review and verify

- Review the diff for compatibility with existing data schemas and unrelated workspace edits.
- Run syntax/static integrity checks and a bounded local pipeline smoke check if required model/data files are present; do not add or run a test suite.
- Document deployment persistence requirements because Render currently has no persistent disk.
