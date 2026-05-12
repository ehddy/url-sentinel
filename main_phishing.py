"""
피싱 사이트 판별 테스트

사용법:
    python main_phishing.py https://suspicious-site.com
    python main_phishing.py
"""

import sys
import time
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, AIMessage
from agent.phishing_graph import build_phishing_graph
from agent.result_writer import save_result
from agent.config import BEDROCK_MODEL_ID

load_dotenv()


def analyze_phishing(url: str) -> dict:
    graph = build_phishing_graph()

    start_time = time.time()
    result = graph.invoke({
        "url": url,
        "messages": [
            HumanMessage(content=f"다음 URL이 피싱 사이트인지 분석해주세요: {url}")
        ],
        "category": None,
        "confidence": None,
        "evidence_summary": None,
    })
    elapsed = round(time.time() - start_time, 2)

    # 모든 AIMessage에서 토큰 사용량 합산
    input_tokens = 0
    output_tokens = 0
    llm_calls = 0
    for msg in result.get("messages", []):
        if isinstance(msg, AIMessage) and msg.usage_metadata:
            input_tokens += msg.usage_metadata.get("input_tokens", 0)
            output_tokens += msg.usage_metadata.get("output_tokens", 0)
            llm_calls += 1

    result["model_id"] = BEDROCK_MODEL_ID
    result["token_usage"] = {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": input_tokens + output_tokens,
        "llm_calls": llm_calls,
    }
    result["processing_time_seconds"] = elapsed

    return result


if __name__ == "__main__":
    if len(sys.argv) > 1:
        target_url = sys.argv[1]
    else:
        target_url = "https://www.naver.com"

    print(f"\n🔍 피싱 분석 시작: {target_url}")
    result = analyze_phishing(target_url)

    usage = result.get("token_usage", {})
    print(f"\n{'='*50}")
    print(f"  🛡️ 피싱 판별 결과")
    print(f"{'='*50}")
    print(f"  URL:      {result['url']}")
    print(f"  판별:      {result.get('category', '(미판별)')}")
    print(f"  신뢰도:    {result.get('confidence', '(없음)')}")
    print(f"  근거:      {result.get('evidence_summary', '(없음)')}")
    print(f"{'='*50}")
    print(f"  🤖 모델:   {result.get('model_id')}")
    print(f"  ⏱️  처리시간: {result.get('processing_time_seconds')}초")
    print(f"  🔢 토큰:   입력 {usage.get('input_tokens', 0):,} / 출력 {usage.get('output_tokens', 0):,} / 합계 {usage.get('total_tokens', 0):,} (LLM 호출 {usage.get('llm_calls', 0)}회)")
    print(f"{'='*50}")

    saved_path = save_result("phishing", result)
    print(f"\n  결과 저장: {saved_path}")