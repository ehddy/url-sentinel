"""
에이전트 State 스키마
"""


from typing import Annotated, TypedDict
from langgraph.graph.message import add_messages 

class SiteAnalysisState(TypedDict):
    """
    사이트 분석 상태

    # add_messages Reducer: 새 메시지가 기존 리스트에 "추가"됨 (덮어쓰기 아님)
    # LLM 응답, Tool 호출 요청, Tool 실행 결과가 모두 여기에 쌓암

    """
    messages: Annotated[list[dict], add_messages]

    # 입력 
    url: str # 분석 대상 URL 

    # 최종 출력
    category: str | None
    # "adult" | "gamble" | "fraud_verify" | "link_hub" | "harmful_other" | "safe"

    confidence: float | None # 0.0`~1.0 사이의 신뢰도 점수`
    evidence_summary: str | None # 판별 근거 요약(한국어)

    