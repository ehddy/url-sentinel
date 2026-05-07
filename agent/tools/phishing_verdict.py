"""
Tool: phishing_verdict — 피싱 사이트 최종 판별
"""

import json
from langchain_core.tools import tool


@tool
def phishing_verdict(
    category: str,
    confidence: float,
    evidence_summary: str,
) -> str:
    """
    피싱 사이트 여부에 대한 최종 판별을 내립니다.
    충분한 근거를 수집한 후 호출하세요.
    이 도구를 호출하면 분석이 종료됩니다.

    Args:
        category: 반드시 'phishing'(피싱) 또는 'safe'(정상) 중 하나
        confidence: 판별 신뢰도 (0.0 ~ 1.0)
        evidence_summary: 판별 근거 요약 (한국어, 핵심만 간결하게)
    """
    if category not in ("phishing", "safe"):
        return json.dumps({
            "success": False,
            "error": f"잘못된 카테고리: '{category}'. 'phishing' 또는 'safe'만 가능합니다.",
        }, ensure_ascii=False)

    confidence = max(0.0, min(1.0, round(confidence, 2)))

    result = {
        "success": True,
        "category": category,
        "category_label": "피싱" if category == "phishing" else "정상",
        "confidence": confidence,
        "evidence_summary": evidence_summary,
    }

    print(f"\n🏁 [PHISHING VERDICT] {category} (confidence: {confidence})")
    print(f"   근거: {evidence_summary[:100]}")

    return json.dumps(result, ensure_ascii=False)