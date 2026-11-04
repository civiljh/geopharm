# GeoPharm 공개 배포

이 저장소는 Render의 Python Web Service 설정(`render.yaml`)을 포함합니다.

## 배포

1. 프로젝트를 GitHub 저장소에 올립니다. `data/raw/medicinal_plants.csv`와 공개 화면에서 사용하는 `data/processed` CSV 파일도 저장소에 포함되어 있는지 확인하세요.
2. Render에서 **New → Blueprint**를 선택하고 저장소를 연결합니다.
3. Render가 `render.yaml` 설정을 읽어 서비스를 생성하면 배포된 `onrender.com` 주소를 열어 확인합니다.

배포에 필요한 패키지 설치와 운영 서버 실행은 Blueprint에 설정되어 있습니다. 공개 방문자는 등록된 식물 데이터를 조회할 수 있습니다. 새 식물 분석은 여러 스크립트를 실행하고 서버 데이터를 갱신하므로 Render에서는 기본적으로 꺼져 있습니다. 공개 서비스에서 켜면 누구나 장시간 작업을 시작하고 서버 데이터를 변경할 수 있으니, 작업량 제한과 별도 작업 큐를 마련한 뒤 Render 환경 변수 `GEOPHARM_ENABLE_PLANT_PIPELINE`을 `true`로 설정하세요. 로컬에서는 별도 설정이 없으면 파이프라인이 켜집니다.

## Windows에서 로컬 확인

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m waitress --listen=127.0.0.1:5000 app:app
```

그 다음 브라우저에서 `http://127.0.0.1:5000`을 열어 확인하세요. 터미널에서 `Ctrl+C`를 누르면 서버가 종료됩니다. 새 터미널을 열어야 할 수도 있습니다.

실제 공개 URL을 만들려면 Git 저장소와 호스팅 계정 연결이 필요합니다. 이 프로젝트 폴더만으로는 외부 계정에 배포할 수 없습니다.
