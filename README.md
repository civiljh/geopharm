# GeoPharm

## English

**GeoPharm** is a research web prototype for exploring traditional medicinal-plant information, plant-associated compounds, predicted protein targets, and observation-based distribution data in one place. The current implementation focuses on targets and candidates related to type 2 diabetes mellitus.

> This project primarily addresses EthnoHack 2026's **Natural Products for Drug Discovery** track and also relates to **Biodiversity & Sustainability** through its plant-observation distribution view. It is a research prototype, not a clinically validated treatment, medical device, or source of medical advice.

## Problem

Information about medicinal plants, their reported natural products, biological targets, and species observations is spread across multiple databases. GeoPharm connects these data so users can search for plants and explore disease-related targets, model-ranked compound candidates, and distribution observations on a map. The goal is to support candidate discovery for follow-up literature review and experimental validation.

## Implemented Features and Progress

### Implemented

- Flask web interface with plant and disease search pages
- Light and dark theme toggle on the main and disease pages, with the selected preference saved in the browser
- Local CSV data linking plants, compounds, protein targets, and prediction records
- Type 2 diabetes plant prioritization, targets, compound candidates, and detailed predictions
- Search for diseases and associated targets through Open Targets, and register other diseases and targets
- Generate plant and compound predictions for registered disease targets and view candidate plants by disease
- Plant distribution map using GBIF and iNaturalist observation data
- When the pipeline is enabled, resolve new plant-name candidates and start compound collection and analysis
- Render deployment configuration (`render.yaml`) and Gunicorn setup
- External data-source links displayed at the bottom of web pages

### Hackathon Feature Progress

- [Complete] **Expanded disease search and analysis:** Search for diseases beyond type 2 diabetes through Open Targets, select and register associated targets, generate predictions using registered targets, and view candidate plants for that disease.
- [Complete] **Theme and source attribution:** Switch between light and dark themes, with the selected theme saved in the browser. Data-source links are displayed at the bottom of the pages.

New features will continue to be tracked here as `[Planned]`, `[In progress]`, or `[Complete]`.

The repository also includes scripts in `src/` for data collection, cleaning, linking, feature generation, prediction, and summarization, along with files under `data/raw/` and `data/processed/`. The public deployment configuration disables the pipeline with `GEOPHARM_ENABLE_PLANT_PIPELINE=false` so visitors cannot trigger operations that modify data files.

## Technology Stack

- Python 3.12 recommended
- Flask: web application and JSON API
- pandas: tabular data processing
- scikit-learn and joblib: saved machine-learning models and prediction pipeline support
- RDKit: molecular-structure-based feature processing
- requests: HTTP requests in data-collection scripts
- Gunicorn: WSGI server for Render deployment
- Leaflet and MarkerCluster: map display, loaded from the unpkg CDN in the browser

Package version ranges are listed in [`requirements.txt`](requirements.txt), and deployment commands are in [`render.yaml`](render.yaml).

## Installation and Local Run

Run these commands from the repository root.

### Windows PowerShell

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m waitress --listen=127.0.0.1:5000 app:app
```

### macOS / Linux

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m waitress --listen=127.0.0.1:5000 app:app
```

Open <http://127.0.0.1:5000> in a browser. The app reads its data from the repository's `data/` directory. Some pages or API responses may be empty if required CSV files are missing. RDKit installation can vary by operating system and Python version.

### Optional New-Plant Analysis Pipeline

The pipeline is enabled by default in the application code, but the public deployment environment variable in `render.yaml` disables it. To use new-plant name lookup, registration, and analysis locally, set this variable in the terminal before starting the server:

```powershell
$env:GEOPHARM_ENABLE_PLANT_PIPELINE = "true"
```

```bash
export GEOPHARM_ENABLE_PLANT_PIPELINE=true
```

Then start the server using the command above. This flow makes requests to external services and can create or update local data files, so enable it only in a development environment where those changes are acceptable. No separate API token is required by the code currently inspected. Check each service's terms and request limits.

## App API

All endpoints are provided by the app without separate authentication. Search results and detail records are based on local data files in the repository.

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/api/plant-search?q={query}` | Plant-name autocomplete. Omitting `q` returns the search list |
| `GET` | `/api/plant-name-resolve?q={English_name}` | Candidate scientific names from external name lookup. Returns `503` when the pipeline is disabled |
| `GET` | `/api/disease-search?q={query}` | Disease-name autocomplete |
| `GET` | `/api/disease-lookup?q={disease_name}` | Search disease names through Open Targets. Pass `disease_id` to return associated targets |
| `POST` | `/api/diseases` | Register a disease and selected targets; runs the prediction pipeline when enabled |
| `GET` | `/disease?disease={disease_name}` | Disease-related targets and predicted candidates page |
| `GET` | `/api/ai-detail/{plant_id}` | Main predicted compound records for a plant |
| `GET` | `/api/ai-full/{plant_id}` | All compound and target prediction records for a plant |
| `GET` | `/api/distribution/{plant_id}` | Distribution observation records for a plant |

Responses are JSON. If prediction or distribution data is unavailable, an endpoint may return an empty `records` list. The web app is available at `/`.

`/api/disease-lookup` calls the public Open Targets GraphQL API. `/api/diseases` saves registrations to `data/processed/disease_catalog.csv` and runs the prediction pipeline when `GEOPHARM_ENABLE_DISEASE_PREDICTIONS` is enabled; this setting defaults to enabled. On deployments with an ephemeral filesystem, registrations and generated data may not persist after a service restart.

## Data and External Services

The data-collection and linking code and the files currently included in the repository are associated with these public databases and services:

- [KNApSAcK](https://www.knapsackfamily.com/): plant and natural-product associations
- [PubChem](https://pubchem.ncbi.nlm.nih.gov/): compound identifiers and structures
- [ChEMBL](https://www.ebi.ac.uk/chembl/): bioactivity and drug-target information
- [BindingDB](https://www.bindingdb.org/): binding-affinity data
- [UniProt](https://www.uniprot.org/): protein targets and sequence information
- [GBIF](https://www.gbif.org/): biodiversity and distribution observations
- [iNaturalist](https://www.inaturalist.org/): species observations and name lookup
- [Open Targets](https://platform.opentargets.org/): disease and associated-target lookup

`data/raw/` contains source or intermediate collected data, while `data/processed/` contains cleaned, linked, and analyzed results. Provenance, licenses, versions, and access dates have not yet been normalized for every individual file. Before external submission, check each dataset's source, license, and redistribution terms, and add any required citations and access dates. Traditional and Indigenous knowledge requires particular care with provenance, cultural context, access restrictions, and sensitivities.

The map uses [Leaflet](https://leafletjs.com/) and [Leaflet.markercluster](https://github.com/Leaflet/Leaflet.markercluster), and requests basemap tiles from [Esri World Street Map](https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer). The browser must connect to the external servers that provide these libraries and map tiles. Follow each service's license and terms of use.

## API Keys and Secrets

The web app and data-collection code currently inspected do not require API keys or tokens. They use public APIs and data endpoints. The network-based plant-processing feature only requires the `GEOPHARM_ENABLE_PLANT_PIPELINE` setting, which is not a secret.

If an authenticated external service is added later, read its key from a local environment variable or `.env` file; never put it in code or the repository. `.env` and `.env.*` are excluded in `.gitignore`. For deployment, use the platform's secret environment-variable settings and document where to obtain and how to configure the key. If a key is committed, deleting it from the file is not enough: revoke and replace it.

## Models, AI Use, and Limitations

The repository contains RDKit-based molecular features, scikit-learn Random Forest training and prediction code, scripts using IC50 data and protein features, and precomputed candidate scores and results. The app displays precomputed prediction files to support candidate prioritization. This does not mean that a new large generative AI model was trained or that the results have been experimentally validated. No calls to an external generative AI service were found in the app code at the time this README was written. If generative AI or AI-assisted tools were used during development, disclose their actual scope and contribution in this section before final submission.

Predicted pChEMBL values and ranking scores are computational candidate-screening results. They do not demonstrate actual binding, in-vivo efficacy, safety, or clinical effect. Consider data bias and missingness, uncertainty in structure-to-target links, and model generalizability; further experiments and expert review are needed. Do not use this project for diagnosis, treatment decisions, or medical advice.

## Deployment

Connect the repository to Render to use the root `render.yaml` Blueprint configuration. The build command is `pip install -r requirements.txt`, the start command uses Gunicorn, and `/` is the health-check path. The default Render configuration disables the new-plant processing pipeline. See [`DEPLOY.md`](DEPLOY.md) for deployment details.

## Presentation and Submission Materials

- Demo video (up to 10 minutes): **(https://www.youtube.com/watch?v=kjiLTRrmioU)**
- Presentation slides (up to 10 slides): **Add link before submission**
- Devpost project page: **(https://geopharm.onrender.com/)**
- Public GitHub repository: **(https://github.com/civiljh/makeathon-2026-geopharm-Natural-Products-and-Drug-Discovery)**

Before submission, check repository visibility, team-member listing, the links above, and data licenses and sources. The EthnoHack rules also require a pitch video of no more than 10 minutes and a presentation of no more than 10 slides.

## Contributions and Development History

Use purpose-specific branches and descriptive commit messages, and make frequent commits in meaningful units. The Git history and team information cannot be verified from this README alone, so disclose which parts were created or modified during the hackathon and which code, libraries, and data already existed on the submission page or in a contribution record.

## License

The license for the project itself and the individual licenses for included data have not yet been confirmed in this README. Check redistribution terms, then add an appropriate license file and data-source information to the repository.

---

# GeoPharm (한국어 원문)

**GeoPharm**은 전통 약용식물 정보, 식물에 연결된 화합물, 단백질 표적 예측, 관찰 기반 분포 정보를 한곳에서 탐색하는 연구용 웹 프로토타입입니다. 현재 구현은 제2형 당뇨병(Type 2 diabetes mellitus) 관련 표적과 후보를 중심으로 구성되어 있습니다.

> 이 프로젝트는 EthnoHack 2026의 **Natural Products for Drug Discovery** 트랙을 주 대상으로 하며, 식물 관찰 분포를 보여주는 범위에서 **Biodiversity & Sustainability**와도 관련됩니다. 아직 연구용 프로토타입이며, 임상적으로 검증된 치료법이나 의료기기 또는 의료 조언이 아닙니다.

## 해결하려는 문제

약용식물, 그 안에 보고된 천연물, 생물학적 표적, 생물종 관찰 기록은 여러 데이터베이스에 나뉘어 있습니다. GeoPharm은 이 정보를 연결해 사용자가 식물 이름을 검색하고, 제2형 당뇨병와 같이 질병 관련 표적과 모델이 우선순위를 매긴 화합물 후보 및 지도상의 분포 기록을 살펴볼 수 있도록 합니다. 목표는 후속 문헌 조사와 실험 검증을 위한 후보 탐색을 돕는 것입니다.

## 현재 구현된 기능과 진행 상황

### 구현 완료

- Flask 기반 웹 인터페이스와 식물 검색, 질병 검색 화면
- 메인 화면과 질병 화면의 라이트·다크 모드 전환 및 브라우저 설정 저장
- 식물·화합물·표적 단백질·예측 레코드를 연결한 로컬 CSV 데이터
- 제2형 당뇨병 관련 식물 우선순위, 표적, 화합물 후보 및 상세 예측 보기
- Open Targets에서 질병명과 연관 표적을 조회하고, 다른 질병과 표적을 등록하는 기능
- 등록한 질병 표적에 대한 식물·화합물 예측 생성과 질병별 후보 식물 조회
- GBIF 및 iNaturalist 관찰 자료를 이용한 식물 분포 지도
- 파이프라인이 활성화된 경우, 새 식물 이름 후보를 확인하고 관련 화합물 수집 및 분석을 시작하는 흐름
- Render 배포 설정(`render.yaml`)과 Gunicorn 실행 구성
- 웹 화면 하단에 외부 데이터 출처 링크 표시

### 해커톤 기간 중 추가 기능 진행 상황

- [완료] **질병 검색 및 분석 확장:** 제2형 당뇨병 외 질병을 Open Targets에서 검색하고, 관련 표적을 선택해 등록할 수 있습니다. 등록된 표적을 이용해 예측을 생성하고 해당 질병의 후보 식물을 조회합니다.
- [완료] **화면 테마 및 출처 표시:** 라이트·다크 모드를 전환할 수 있고 선택한 테마는 브라우저에 저장됩니다. 데이터 출처 링크를 화면 하단에 표시합니다.

추가 기능은 `[예정]`, `[진행 중]`, `[완료]` 상태로 구분해 이 목록에 계속 기록합니다.

이 저장소에는 수집·정제·연결·특징 생성·예측·요약 작업을 위한 `src/` 스크립트와 `data/raw/`, `data/processed/` 자료가 포함되어 있습니다. 공개 배포 설정은 `GEOPHARM_ENABLE_PLANT_PIPELINE=false`로 파이프라인을 비활성화합니다. 공개 방문자가 데이터 파일을 변경하는 작업을 실행하지 않도록 한 기본값입니다.

## 기술 스택

- Python 3.12 권장
- Flask: 웹 애플리케이션 및 JSON API
- pandas: 표 형식 데이터 처리
- scikit-learn, joblib: 저장된 머신러닝 모델과 예측 파이프라인 지원
- RDKit: 화합물 구조 기반 특징 처리
- requests: 데이터 수집 스크립트의 HTTP 요청
- Gunicorn: Render 배포용 WSGI 서버
- Leaflet 및 MarkerCluster: 지도 표시 (브라우저에서 unpkg CDN을 통해 로드)

정확한 패키지 범위는 [`requirements.txt`](requirements.txt), 배포 명령은 [`render.yaml`](render.yaml)에 기록되어 있습니다.

## 설치 및 로컬 실행

저장소 루트에서 실행합니다.

### Windows PowerShell

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m waitress --listen=127.0.0.1:5000 app:app
```

### macOS / Linux

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m waitress --listen=127.0.0.1:5000 app:app
```

브라우저에서 <http://127.0.0.1:5000>을 엽니다. 실행에 필요한 데이터는 저장소의 `data/` 경로에서 읽습니다. 필요한 CSV가 없으면 일부 화면이나 API 결과가 비어 있을 수 있습니다. RDKit은 운영체제와 Python 버전에 따라 설치 환경이 달라질 수 있습니다.

### 선택적 새 식물 분석 파이프라인

기본적으로 앱의 코드상 파이프라인은 활성화되어 있지만, `render.yaml`의 공개 배포 환경 변수는 이를 비활성화합니다. 로컬에서 새 식물 이름 조회와 등록·분석 흐름을 사용하려면 실행하는 터미널에서 다음 환경 변수를 설정합니다.

```powershell
$env:GEOPHARM_ENABLE_PLANT_PIPELINE = "true"
```

```bash
export GEOPHARM_ENABLE_PLANT_PIPELINE=true
```

그 후 위 실행 명령으로 서버를 시작합니다. 이 흐름은 외부 서비스에 요청하고 로컬 데이터 파일을 생성·갱신할 수 있으므로, 쓰기 권한이 있는 개발 환경에서만 활성화하세요. 별도의 API 토큰이 필요한 구성은 현재 코드에서 확인되지 않았습니다. 외부 서비스의 이용 조건이나 요청 제한은 서비스별로 확인해야 합니다.

## 앱 API

모든 엔드포인트는 별도 인증 없이 앱에서 제공합니다. 검색 결과와 상세 정보는 저장소의 로컬 데이터 파일을 기반으로 합니다.

| 메서드 | 경로 | 설명 |
| --- | --- | --- |
| `GET` | `/api/plant-search?q={검색어}` | 식물명 자동완성. `q` 생략 시 검색 목록 반환 |
| `GET` | `/api/plant-name-resolve?q={영문명}` | 외부 이름 조회를 통한 학명 후보. 파이프라인이 꺼져 있으면 `503` |
| `GET` | `/api/disease-search?q={검색어}` | 질병명 자동완성 |
| `GET` | `/api/disease-lookup?q={질병명}` | Open Targets 질병명 검색. `disease_id`를 전달하면 연관 표적을 반환 |
| `POST` | `/api/diseases` | 질병과 선택한 표적을 등록하고 설정에 따라 예측 파이프라인 실행 |
| `GET` | `/disease?disease={질병명}` | 질병 관련 표적 및 예측 후보 화면 |
| `GET` | `/api/ai-detail/{plant_id}` | 식물별 주요 예측 화합물 레코드 |
| `GET` | `/api/ai-full/{plant_id}` | 식물별 전체 화합물·표적 예측 레코드 |
| `GET` | `/api/distribution/{plant_id}` | 식물별 분포 관찰 레코드 |

응답은 JSON이며, 예측 또는 분포 데이터가 없으면 빈 `records` 목록을 반환할 수 있습니다. 웹 앱은 `/`에서 열립니다.

`/api/disease-lookup`은 Open Targets의 공개 GraphQL API를 호출합니다. `/api/diseases`는 등록 내용을 `data/processed/disease_catalog.csv`에 저장하고, `GEOPHARM_ENABLE_DISEASE_PREDICTIONS` 환경 변수가 활성화된 경우 예측 파이프라인을 실행합니다. 기본값은 활성화입니다. 임시 파일 시스템을 사용하는 배포에서는 등록 결과와 생성 데이터가 서비스 재시작 후 보존되지 않을 수 있습니다.

## 데이터·외부 서비스 및 출처

데이터 수집·연결 코드와 현재 포함된 파일은 다음 공개 데이터베이스 및 서비스와 관련되어 있습니다.

- [KNApSAcK](https://www.knapsackfamily.com/): 식물과 천연물 연결 정보
- [PubChem](https://pubchem.ncbi.nlm.nih.gov/): 화합물 식별 정보 및 구조
- [ChEMBL](https://www.ebi.ac.uk/chembl/): 생리활성 및 약물 표적 정보
- [BindingDB](https://www.bindingdb.org/): 결합 친화도 자료
- [UniProt](https://www.uniprot.org/): 단백질 표적 및 서열 정보
- [GBIF](https://www.gbif.org/): 생물다양성 및 분포 관찰 자료
- [iNaturalist](https://www.inaturalist.org/): 생물종 관찰 및 이름 후보 조회

`data/raw/`에는 원자료 또는 중간 수집 자료가, `data/processed/`에는 정제·연결·분석 결과가 있습니다. 개별 파일의 레코드별 출처·라이선스·버전·접근일이 아직 모두 정규화된 형태로 기록되어 있지는 않습니다. 외부 제출 전에 각 데이터셋의 출처, 라이선스 및 재배포 조건을 확인하고, 요구되는 인용과 접근일을 보완해야 합니다. 특히 전통·토착 지식과 관련한 자료는 출처, 문화적 맥락, 접근 제한 및 민감성을 확인해야 합니다.

지도 화면은 [Leaflet](https://leafletjs.com/)과 [Leaflet.markercluster](https://github.com/Leaflet/Leaflet.markercluster)를 사용하고, 배경 타일은 [Esri World Street Map](https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer)을 요청합니다. 브라우저는 이 라이브러리와 지도 타일을 제공하는 외부 서버에 연결해야 합니다. 각 서비스의 라이선스와 사용 조건을 준수하세요.

## API 키와 비밀정보

현재 확인된 웹 앱과 데이터 수집 코드에는 필수 API 키 또는 토큰이 없습니다. 공개 API와 데이터 엔드포인트를 사용하며, 네트워크 기반 식물 처리 기능에는 `GEOPHARM_ENABLE_PLANT_PIPELINE` 설정만 필요합니다. 이 값은 비밀정보가 아닙니다.

향후 인증이 필요한 외부 서비스를 추가하면 키를 코드나 저장소에 넣지 말고, 로컬 환경 변수 또는 `.env` 파일에서 읽도록 구성하세요. `.env`와 `.env.*`는 `.gitignore`에서 제외되어 있습니다. 배포 환경에서는 해당 플랫폼의 비밀 환경 변수 설정을 이용하고, README에 키 발급 위치와 설정 방법을 문서화해야 합니다. 키를 커밋했다면 파일에서 지우는 것만으로 충분하지 않으므로 해당 키를 폐기하고 재발급하세요.

## 모델, AI 사용 및 한계

저장소에는 RDKit 기반 분자 특징, scikit-learn Random Forest 학습·예측 코드, IC50 자료 및 단백질 특징을 사용하는 스크립트, 사전 계산된 후보 점수와 결과 파일이 있습니다. 앱은 사전 계산된 예측 파일을 표시하고 우선순위 탐색을 돕습니다. 이는 새로 학습된 대규모 생성형 AI 모델이나 실험 검증 결과를 뜻하지 않습니다. 이 README 작성 시점에 외부 생성형 AI 서비스 호출은 앱 코드에서 확인되지 않았습니다. 개발 과정에서 생성형 AI 또는 AI 보조 도구를 사용했다면 실제 사용 범위와 기여를 최종 제출 전에 이 절에 구체적으로 공개하세요.

예측 pChEMBL 및 순위 점수는 계산상 후보 선별 결과입니다. 실제 결합, 생체 내 효능, 안전성 또는 임상 효과를 입증하지 않습니다. 데이터의 편향·누락, 구조와 표적 연결의 불확실성, 모델 일반화 성능을 고려하고 후속 실험과 전문가 검토가 필요합니다. 이 프로젝트를 진단·치료 결정이나 의료 조언에 사용하지 마세요.

## 배포

저장소를 Render에 연결하면 루트의 `render.yaml` Blueprint 설정을 사용할 수 있습니다. 빌드는 `pip install -r requirements.txt`, 시작 명령은 Gunicorn이며 `/`를 헬스 체크 경로로 사용합니다. Render의 기본 설정은 새 식물 처리 파이프라인을 비활성화합니다. 배포 세부 사항은 [`DEPLOY.md`](DEPLOY.md)를 참고하세요.

## 발표 및 제출 자료

- 데모 영상 (10분 이내): **(https://www.youtube.com/watch?v=kjiLTRrmioU)**
- 발표 자료 (10장 이내): **제출 전 링크 추가**
- Devpost 프로젝트 페이지: **(https://geopharm.onrender.com/)**
- 공개 GitHub 저장소: **(https://github.com/civiljh/makeathon-2026-geopharm-Natural-Products-and-Drug-Discovery)**

제출 전 저장소 공개 여부, 팀원 등록, 위 링크, 데이터 라이선스와 출처를 확인하세요. EthnoHack 룰북은 최대 10분 피치 영상과 최대 10장 발표 자료도 요구합니다.

## 기여 및 개발 기록

개발 시 목적이 분명한 브랜치와 설명적인 커밋 메시지를 사용하고, 의미 있는 변경 단위로 자주 커밋하는 방식을 권장합니다. 현재 저장소의 Git 이력과 팀 정보는 README만으로 검증할 수 없으므로, 해커톤 중 작성·수정한 부분과 기존 코드·라이브러리·자료를 구분해 제출 페이지 또는 별도 기여 기록에 공개하세요.

## 라이선스

프로젝트 자체의 라이선스와 포함 데이터의 개별 라이선스는 아직 이 README에서 확정하지 않았습니다. 재배포 조건을 확인한 뒤 저장소에 적절한 라이선스 파일과 데이터별 출처 정보를 추가하세요.
