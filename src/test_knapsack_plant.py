import requests
from bs4 import BeautifulSoup

PLANT_NAME = "Momordica charantia"

URL = (
    "https://www.knapsackfamily.com/"
    "knapsack_core/info.php"
)

PARAMS = {
    "sname": "organism",
    "word": PLANT_NAME
}

print("=" * 60)
print("KNApSAcK 식물 검색 테스트")
print("=" * 60)
print()
print("검색 식물:", PLANT_NAME)
print()

try:
    response = requests.get(
        URL,
        params=PARAMS,
        timeout=30
    )

    print("HTTP 상태 코드:", response.status_code)
    print("실제 요청 주소:")
    print(response.url)
    print()

    response.raise_for_status()

    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )

    page_text = soup.get_text(" ", strip=True)

    print("페이지 가져오기: 성공")
    print()

    if PLANT_NAME.lower() in page_text.lower():
        print("검색 결과에서 식물 이름 발견: YES")
    else:
        print("검색 결과에서 식물 이름 발견: NO")

    print()
    print("페이지 제목:")
    print(soup.title.get_text(strip=True) if soup.title else "없음")

    print()
    print("=" * 60)
    print("테스트 완료")
    print("=" * 60)

except Exception as e:
    print()
    print("오류가 발생했습니다.")
    print(type(e).__name__)
    print(str(e))