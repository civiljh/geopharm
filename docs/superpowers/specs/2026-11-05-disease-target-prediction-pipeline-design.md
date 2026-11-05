# Disease Target Prediction Pipeline Design

## Goal

When a user registers a disease, generate plant compound predictions for its selected human targets that are not already covered by the stored prediction dataset. Make those predictions available to disease and plant search pages. All new browser-visible text must be English.

## User flow

1. The user selects disease targets and submits the registration form.
2. The server resolves each target to a human UniProt accession and protein sequence, reusing local mappings and sequences first and querying UniProt when needed.
3. The server derives the same 26 protein sequence features used during model training.
4. It predicts compound-target values with the existing trained model in bounded batches, skipping target/compound pairs already present.
5. It stores the generated records in the existing human prediction dataset, records target mapping and prediction status, then returns the disease and analysis outcome. The page opens after processing finishes.
6. Unresolvable targets are retained in the disease catalog and reported as unavailable; other resolvable targets continue processing.

## Data and scoring

- Reuse the existing plant-compound prediction-ready table, Morgan fingerprints, protein feature schema, and trained model. Do not retrain the model during disease registration.
- Use canonical human UniProt accessions. Prefer reviewed UniProtKB records and deterministic selection when multiple records match a gene symbol.
- Deduplicate generated predictions by `(ChEMBL_ID, UniProt_ID)` and preserve the plant, compound, protein, gene, organism, and review fields consumed by current pages.
- Mark new predictions as model-generated and extrapolated to a target, so the UI does not present them as experimentally confirmed effects.
- The existing disease ranking code will consume the newly appended target-linked records; no separate prediction formula is introduced in this pipeline.

## Failure and limits

- Cap registration at the existing 20 targets and reject invalid targets before prediction.
- Predict in bounded batches to control memory use.
- If UniProt lookup, sequence retrieval, model loading, or prediction fails for one target, keep the disease registration and return a per-target failure status where possible. Do not discard successful target predictions.
- Avoid duplicate target work and write the prediction CSV atomically to prevent partial files.
- The deployment currently has no persistent disk configured. Runtime CSV additions can be lost on service restart; durable hosted results require persistent storage configuration.

## Out of scope

- Training or validating a new model.
- Recomputing all historical plant-target predictions.
- Adding new external databases beyond UniProt for target accession and sequence resolution.
- Claiming therapeutic efficacy or clinical evidence from model predictions.

## Verification

- Verify feature columns match the model's expected training features.
- Verify batching, target/compound deduplication, partial target failures, and atomic persistence with focused checks.
- Verify the disease registration response exposes English status messages and generated results are visible on disease and plant pages.
