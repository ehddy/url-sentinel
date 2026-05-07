"""
단일 URL 분석 테스트

사용법:
    venv\Scripts\activate
    python main.py https://example.com
    python main.py  (기본 테스트 URL 사용)
"""

import sys
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from agent.graph import build_graph
from agent.result_writer import save_result

load_dotenv()


def analyze_url(url: str) -> dict:
    graph = build_graph()

    result = graph.invoke({
        "url": url,
        "messages": [
            HumanMessage(content=f"다음 URL을 분석해주세요: {url}")
        ],
        "category": None,
        "confidence": None,
        "evidence_summary": None,
    })

    return result


if __name__ == "__main__":
    if len(sys.argv) > 1:
        target_url = sys.argv[1]
    else:
        target_url = "https://www.naver.com"

    print(f"\n🔍 분석 시작: {target_url}")
    result = analyze_url(target_url)

    print(f"\n{'='*50}")
    print(f"  📊 최종 결과")
    print(f"{'='*50}")
    print(f"  URL:      {result['url']}")
    print(f"  카테고리:  {result.get('category', '(미판별)')}")
    print(f"  신뢰도:    {result.get('confidence', '(없음)')}")
    print(f"  근거:      {result.get('evidence_summary', '(없음)')}")
    print(f"{'='*50}")

    saved_path = save_result("category", result)
    print(f"\n  결과 저장: {saved_path}")