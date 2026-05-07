"""
Tool: google_search — Google 검색으로 도메인 평판 조회

해당 도메인을 구글에 검색하여 최근 관련 게시글을 가져옵니다.
활용 예시:
- 도메인이 "먹튀", "사기" 등으로 언급되고 있는지 확인
- 크롤링 결과를 외부 정보로 교차 검증
- 사이트가 어떤 맥락에서 언급되는지 파악
"""


import requests
from langchain_core.tools import tool
from agent.config import GOOGLE_API_KEY, GOOGLE_CX, GOOGLE_SEARCH_DAYS

@tool
def google_search(query: str) -> str:
    """
    Google에서 도메인이나 키워드를 검색하여 최근 관련 결과를 가져옵니다.
    도메인을 검색하면 해당 사이트가 외부에서 어떻게 언급되는지 확인할 수 있습니다.
    예: '먹튀', '사기', '불법' 등의 맥락으로 언급되는지 파악하는 데 유용합니다.
    도메인 또는 자유 키워드를 입력하세요.
    """

    if not GOOGLE_API_KEY or not GOOGLE_CX:
        return "[Google 검색 실패] API 키 또는 CX가 설정되지 않았습니다. .env를 확인하세요."

    print(f"🔎 [GOOGLE] 검색: {query} (최근 {GOOGLE_SEARCH_DAYS}일)")

    try:
        params = {
            "key": GOOGLE_API_KEY,
            "cx": GOOGLE_CX,
            "q": query,
            "gl": "kr",
            "lr": "lang_ko",
            "num": 10,
            "dateRestrict": f"d{GOOGLE_SEARCH_DAYS}",
        }

        response = requests.get(
            "https://www.googleapis.com/customsearch/v1",
            params=params,
            timeout=15,
        )
        response.raise_for_status()
        data = response.json()

    except requests.exceptions.HTTPError as e:
        status = e.response.status_code if e.response else "unknown"
        return f"[Google 검색 실패] HTTP {status}: {str(e)[:80]}"
    except Exception as e:
        return f"[Google 검색 실패] {str(e)[:80]}"

    items = data.get("items", [])

    if not items:
        print(f"✅ [GOOGLE] 검색 결과 없음")
        return f"[Google 검색 결과] '{query}' 관련 최근 {GOOGLE_SEARCH_DAYS}일 이내 결과 없음"

    print(f"✅ [GOOGLE] {len(items)}건 검색됨")

        # 결과 포맷팅
    output = f"[Google 검색 결과] '{query}' — 최근 {GOOGLE_SEARCH_DAYS}일, {len(items)}건\n"

    for i, item in enumerate(items, 1):
        title = item.get("title", "(제목 없음)")
        snippet = item.get("snippet", "").replace("\n", " ").strip()
        link = item.get("link", "")

        output += f"\n{i}. {title}\n"
        output += f"   URL: {link}\n"
        if snippet:
            output += f"   내용: {snippet[:150]}\n"

    return output
