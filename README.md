# GeoPharm

**GeoPharm**은 전통 약용식물 정보, 식물에 연결된 화합물, 단백질 표적 예측, 관찰 기반 분포 정보를 한곳에서 탐색하는 연구용 웹 프로토타입입니다. 현재 구현은 제2형 당뇨병(Type 2 diabetes mellitus) 관련 표적과 후보를 중심으로 구성되어 있습니다.

> 이 프로젝트는 EthnoHack 2026의 **Natural Products for Drug Discovery** 트랙을 주 대상으로 하며, 식물 관찰 분포를 보여주는 범위에서 **Biodiversity & Sustainability**와도 관련됩니다. 아직 연구용 프로토타입이며, 임상적으로 검증된 치료법이나 의료기기 또는 의료 조언이 아닙니다.

## 해결하려는 문제

약용식물, 그 안에 보고된 천연물, 생물학적 표적, 생물종 관찰 기록은 여러 데이터베이스에 나뉘어 있습니다. GeoPharm은 이 정보를 연결해 사용자가 식물 이름을 검색하고, 제2형 당뇨병 관련 표적과 모델이 우선순위를 매긴 화합물 후보 및 지도상의 분포 기록을 살펴볼 수 있도록 합니다. 목표는 후속 문헌 조사와 실험 검증을 위한 후보 탐색을 돕는 것입니다.

## 현재 구현된 기능과 진행 상황

### 구현 완료

- Flask 기반 웹 인터페이스와 식물 검색, 질병 검색 화면
- 식물·화합물·표적 단백질·예측 레코드를 연결한 로컬 CSV 데이터
- 제2형 당뇨병 관련 식물 우선순위, 표적, 화합물 후보 및 상세 예측 보기
- GBIF 및 iNaturalist 관찰 자료를 이용한 식물 분포 지도
- 파이프라인이 활성화된 경우, 새 식물 이름 후보를 확인하고 관련 화합물 수집 및 분석을 시작하는 흐름
- Render 배포 설정(`render.yaml`)과 Gunicorn 실행 구성

### 추가 예정 및 해커톤 기간 중 진행 상황

- [예정] **질병 검색 개선:** 질병명과 지원하는 별칭을 더 쉽게 찾고, 검색 결과를 알아보기 쉽게 표시하도록 검색 흐름을 다듬습니다.
- [예정] **식물 검색 개선:** 국명·영문명·학명 검색과 자동완성 결과를 개선해 원하는 식물 후보를 더 쉽게 찾도록 합니다.

구현을 시작하면 상태를 `[진행 중]`으로, 완료 후에는 `[완료]`로 바꾸고 실제 변경 내용을 덧붙입니다.

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
| `GET` | `/disease?disease={질병명}` | 질병 관련 표적 및 예측 후보 화면 |
| `GET` | `/api/ai-detail/{plant_id}` | 식물별 주요 예측 화합물 레코드 |
| `GET` | `/api/ai-full/{plant_id}` | 식물별 전체 화합물·표적 예측 레코드 |
| `GET` | `/api/distribution/{plant_id}` | 식물별 분포 관찰 레코드 |

응답은 JSON이며, 예측 또는 분포 데이터가 없으면 빈 `records` 목록을 반환할 수 있습니다. 웹 앱은 `/`에서 열립니다.

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

- 데모 영상 (10분 이내): **제출 전 링크 추가**
- 발표 자료 (10장 이내): **제출 전 링크 추가**
- Devpost 프로젝트 페이지: **제출 전 링크 추가**
- 공개 GitHub 저장소: **공개 저장소 생성 후 링크 추가**

제출 전 저장소 공개 여부, 팀원 등록, 위 링크, 데이터 라이선스와 출처를 확인하세요. EthnoHack 룰북은 최대 10분 피치 영상과 최대 10장 발표 자료도 요구합니다.

## 기여 및 개발 기록

개발 시 목적이 분명한 브랜치와 설명적인 커밋 메시지를 사용하고, 의미 있는 변경 단위로 자주 커밋하는 방식을 권장합니다. 현재 저장소의 Git 이력과 팀 정보는 README만으로 검증할 수 없으므로, 해커톤 중 작성·수정한 부분과 기존 코드·라이브러리·자료를 구분해 제출 페이지 또는 별도 기여 기록에 공개하세요.

## 라이선스

프로젝트 자체의 라이선스와 포함 데이터의 개별 라이선스는 아직 이 README에서 확정하지 않았습니다. 재배포 조건을 확인한 뒤 저장소에 적절한 라이선스 파일과 데이터별 출처 정보를 추가하세요.
