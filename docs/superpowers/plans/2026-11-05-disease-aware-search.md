# 질병별 식물 검색 Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax for tracking.

**Goal:** 질병별 표적과 기존 식물 예측 데이터를 연결해 후보 식물을 순위화하고, 질병/식물 검색 화면에서 교차 이동을 제공한다.

**Architecture:** Flask 단일 앱을 유지한다. 질병 및 선택된 표적은 별도 CSV에 영속화하고, Open Targets GraphQL 조회는 서버 측 요청으로 처리한다. 식물별 질병 점수는 저장된 표적과 범용 식물 AI 예측 CSV를 연결해 계산하며, HTML/JavaScript가 질병 등록과 검색 흐름을 노출한다.

**Tech Stack:** Python, Flask, pandas, CSV, Open Targets GraphQL, Jinja, browser JavaScript.

**Spec:** `docs/superpowers/specs/2026-11-05-disease-aware-search-design.md`

## Global Constraints

- 외부 API 장애가 있어도 저장된 질병 검색과 직접 표적 입력은 동작한다.
- 기존 T2D 순위/점수 동작은 보존한다.
- 점수는 표적에 연결된 화합물들의 평균 `Predicted_pChEMBL`로 계산하고 치료 효과 확정으로 표현하지 않는다.
- 저장소 지침상 테스트 파일을 추가하거나 테스트를 실행하지 않는다.

## Review Focus

- Open Targets가 응답하지 않거나 결과가 없을 때 직접 유전자 심볼 입력으로 저장·검색할 수 있는지 — Task 2/3 코드 검토.
- 중복 질병 및 공백/비ASCII 질병명이 카탈로그에 중복 저장되지 않는지 — Task 1 코드 검토.
- 현재 예측 데이터에 없는 UniProt 표적은 순위 결과에 포함되지 않는지 — Task 3 코드 검토.
- URL에 전달된 질병명이 HTML에 안전하게 렌더링되는지, POST/외부 응답에서 표적 입력이 제한되는지 — Task 2/4 코드 검토.
- 새 질병 데이터가 없는 상태에서도 기본 홈과 기존 T2D 검색이 유지되는지 — Task 4/5 코드 검토.

---

### Task 1: 질병 카탈로그 저장소

**Files:**
- Modify: `app.py` disease data paths/loading helpers near `DISEASE_TARGET_LIST`
- Create at runtime: `data/processed/disease_catalog.csv`

**Interfaces:**
- Produce `load_disease_catalog() -> pandas.DataFrame`, `save_disease(name: str, targets: list[dict]) -> dict`, and `list_diseases() -> list[dict]`.
- Persist one row per disease-target pair with `Disease`, `OpenTargets_ID`, `UniProt_ID`, `Gene_Name`, `Protein_Name`, `Association_Score`, and `Source` columns. Keep a disease with no targets as one row with blank target fields.
- Merge the current `t2d_target_list.csv` at load time as the initial catalog so current Type 2 diabetes entries remain discoverable before a new catalog file exists.

- [x] Add CSV loader, normalized disease-name deduplication, and append/update helper without replacing other diseases.
- [x] Ensure registering the same normalized disease updates/merges its selected target records instead of creating duplicate disease rows.
- [x] Route existing `DISEASE_TARGET_LIST` consumers through the combined catalog loader or adapt them to the new catalog representation.

### Task 2: Disease/target lookup and registration APIs

**Files:**
- Modify: `app.py` next to `/api/disease-search`

**Interfaces:**
- Add `lookup_disease_targets(query: str) -> list[dict]` using the official Open Targets GraphQL API over HTTPS, with bounded timeout, a maximum 10 disease matches and a maximum 20 target suggestions per selected disease.
- Add `GET /api/disease-lookup?q=...` returning candidate disease names/IDs and associated target fields (`gene_symbol`, `uniprot_id`, `protein_name`, `association_score`).
- Add `POST /api/diseases` accepting `{name, open_targets_id, targets:[{gene_symbol, uniprot_id, protein_name, association_score}]}`; validate and persist user-confirmed targets via Task 1, then return the canonical disease entry.
- Keep `/api/disease-search?q=` useful with empty `q` by returning the full registered disease list.

- [x] Add server-side GraphQL request and response normalization; convert network/GraphQL errors to a clear 502 response without preventing manual registration.
- [x] Add disease lookup and registration endpoints with field length/count validation and safe JSON errors.
- [x] Return the stored catalog entries from `/api/disease-search`, supporting the existing Korean Type 2 diabetes aliases.

### Task 3: Disease-specific plant scoring

**Files:**
- Modify: `app.py` near prediction loaders and `disease_search()`

**Interfaces:**
- Add `load_plant_target_predictions() -> pandas.DataFrame` reading `data/processed/plant_ai_human_predictions.csv` with UTF-8 BOM support.
- Add `rank_plants_for_disease(disease: str, limit: int = 5) -> list[dict]`; match catalog targets to prediction UniProt IDs or gene symbols, group by `Plant_ID`, then calculate the same T2D formula per disease cohort: 30% normalized maximum prediction + 40% normalized mean prediction + 30% normalized `log1p` distinct compound count, multiplied by `sqrt(compound_count / (compound_count + 10))`. Return `Priority_Score`, rank, compound/target counts, `Compound_Evidence_Level` (30+ High, 10+ Medium, otherwise Low), `Reliability_Category` (30+ High, 10+ Medium, 3+ Low, otherwise Very Low), and plant names. Sort by priority score descending.
- Disease target detail and candidate compounds on `/disease` must come from the selected disease's catalog targets and these generic predictions, not the current T2D-only full prediction file.

- [x] Implement disease-specific plant aggregation and priority, evidence, reliability, and compound metrics from the generic plant prediction file.
- [x] Rank the top five plants and expose score/count metadata to the disease page; empty target/overlap results produce an empty ranking.
- [x] Preserve the existing T2D priority file score when the selected disease is Type 2 diabetes.

### Task 4: Disease search and registration interface

**Files:**
- Modify: `app.py` `DISEASE_HTML`, `/disease`, and disease autocomplete JavaScript

**Interfaces:**
- `/disease?disease=<name>` renders `disease_name`, `targets`, `top_plants`, and `candidates` from Tasks 1 and 3.
- Each top plant link uses `/?plant=<Plant_ID>&disease=<disease name>` so the existing plant route opens its detail page with the disease selected.
- The disease search autocomplete returns all catalog diseases when opened with an empty query.

- [x] Render top five ranked plants in a card before “Related Targets”, with candidate-score context, plant links, and an explanatory AI-screening note.
- [x] Add a no-results registration path: lookup disease candidates, let the user select a disease and review/edit suggested genes, permit manual gene-symbol entry when lookup fails, then POST confirmed entries to `/api/diseases`.
- [x] After successful registration, navigate to `/disease?disease=<canonical name>` and show an explicit no-data state if no usable plant predictions exist.
- [x] Retain registered diseases in disease search suggestions, including on an empty search field.

### Task 5: Disease-aware plant page and logo navigation

**Files:**
- Modify: `app.py` main `HTML` logo/header, disease search form, score/table section, and `index()` route

**Interfaces:**
- `index()` accepts `?plant=<name or Plant_ID>&disease=<disease name>` and provides `disease_options`, `selected_disease`, `selected_disease_score`, and `disease_ranked_plants` to the template.
- The plant disease selector submits the selected disease while retaining the current plant query.
- The home logo is an anchor to `/` with no query parameters.

- [x] Replace the plain-text brand div with an accessible home anchor and ensure disease page brand links to `/` as already intended.
- [x] Add a registered-disease select control at the existing T2D score position; default to T2D and preserve selected disease in the URL.
- [x] For T2D, show the existing priority score/rank. For other diseases, show the Task 3 priority score/rank, Evidence Level, Reliability, and selected-disease plant table; render an explicit empty-data state where appropriate.
- [x] Preserve plant analysis behavior when no `disease` parameter is supplied; show the selector with the selected plant's analysis.
