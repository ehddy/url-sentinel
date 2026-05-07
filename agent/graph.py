"""
에이전트 그래프 조립

Ch3에서 배운 ReAct 패턴을 적용합니다:
    START → agent → (tool_calls?) → tools → agent → ... → END

이 파일 하나가 프로젝트의 핵심입니다.
"""

from agent.config import BEDROCK_MODEL_ID, AWS_REGION

from langchain_aws import ChatBedrockConverse
from langchain_core.messages import SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition

from agent.state import SiteAnalysisState
from agent.tools import all_tools
from agent.prompts import SYSTEM_PROMPT



def build_graph():
    """
    사이트 분석 에이전트 그래프를 생성합니다.

    Returns:
        CompiledStateGraph — invoke() 또는 stream()으로 실행 가능
    """
    # ── LLM 초기화 ──────────────────────
    llm = ChatBedrockConverse(
        model=BEDROCK_MODEL_ID,
        region_name=AWS_REGION,
        temperature=0,
        max_tokens=4096,
    )
    llm_with_tools = llm.bind_tools(all_tools)

    # ── Node ①: agent ───────────────────
    def agent(state: SiteAnalysisState) -> dict:
        """
        LLM을 호출하여 다음 행동을 결정합니다.

        - LLM은 tool_call을 반환하거나 (→ tools 노드로)
        - 텍스트 응답을 반환합니다 (→ END)
        """
        system_msg = SystemMessage(
            content=f"{SYSTEM_PROMPT}\n\n현재 분석 대상 URL: {state['url']}"
        )

        msg_count = len(state["messages"])
        print(f"\n{'='*50}")
        print(f"🤖 [AGENT] LLM 호출 (누적 메시지: {msg_count}개)")
        print(f"{'='*50}")


        response = llm_with_tools.invoke([system_msg] + state["messages"])

        # ── LLM 응답 확인 ──
        if response.tool_calls:
            for tc in response.tool_calls:
                args_preview = str(tc["args"])[:100]
                print(f"🔧 [AGENT] Tool 호출 결정: {tc['name']}({args_preview})")
        else:
            content_preview = str(response.content)[:150]
            print(f"💬 [AGENT] 텍스트 응답 (Tool 호출 없음 → 종료)")
            print(f"   내용: {content_preview}")

        update: dict = {"messages": [response]}

        # make_verdict가 호출되면 State에 결과 기록
        for tc in response.tool_calls:
            if tc["name"] == "make_verdict":
                args = tc["args"]
                update["category"] = args.get("category")
                update["confidence"] = args.get("confidence")
                update["evidence_summary"] = args.get("evidence_summary")
                print(f"📋 [AGENT] 판별 결과 State 기록: {args.get('category')} ({args.get('confidence')})")


        return update

    # ── Node ②: tools ───────────────────
    tool_node = ToolNode(all_tools)

    # ── 그래프 조립 ──────────────────────
    builder = StateGraph(SiteAnalysisState)

    builder.add_node("agent", agent)
    builder.add_node("tools", tool_node)

    builder.add_edge(START, "agent")
    builder.add_conditional_edges("agent", tools_condition)
    builder.add_edge("tools", "agent")

    return builder.compile()