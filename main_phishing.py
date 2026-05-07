"""
피싱 사이트 판별 테스트

사용법:
    python main_phishing.py https://suspicious-site.com
    python main_phishing.py
"""

import sys
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from agent.phishing_graph import build_phishing_graph
from agent.result_writer import save_result

load_dotenv()


def analyze_phishing(url: str) -> dict:
    graph = build_phishing_graph()

    result = graph.invoke({
        "url": url,
        "messages": [
            HumanMessage(content=f"다음 URL이 피싱 사이트인지 분석해주세요: {url}")
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

    print(f"\n🔍 피싱 분석 시작: {target_url}")
    result = analyze_phishing(target_url)

    print(f"\n{'='*50}")
    print(f"  🛡️ 피싱 판별 결과")
    print(f"{'='*50}")
    print(f"  URL:      {result['url']}")
    print(f"  판별:      {result.get('category', '(미판별)')}")
    print(f"  신뢰도:    {result.get('confidence', '(없음)')}")
    print(f"  근거:      {result.get('evidence_summary', '(없음)')}")
    print(f"{'='*50}")

    saved_path = save_result("phishing", result)
    print(f"\n  결과 저장: {saved_path}")