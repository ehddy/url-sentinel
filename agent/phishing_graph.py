"""
피싱 판별 에이전트 그래프
"""

from langchain_aws import ChatBedrockConverse
from langchain_core.messages import SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition

from agent.config import BEDROCK_MODEL_ID, AWS_REGION
from agent.phishing_state import PhishingAnalysisState
from agent.phishing_prompts import PHISHING_SYSTEM_PROMPT

from agent.tools.dns_check import dns_check
from agent.tools.crawl import crawl_page
from agent.tools.whois_lookup import whois_lookup
from agent.tools.google_search import google_search
from agent.tools.screenshot import capture_and_analyze
from agent.tools.phishing_verdict import phishing_verdict
from agent.tools.virustotal import virustotal_check


phishing_tools = [
    dns_check,
    crawl_page,
    whois_lookup,
    google_search,
    capture_and_analyze,
    phishing_verdict,
    virustotal_check,
]


def build_phishing_graph():
    llm = ChatBedrockConverse(
        model=BEDROCK_MODEL_ID,
        region_name=AWS_REGION,
        temperature=0,
        max_tokens=4096,
    )
    llm_with_tools = llm.bind_tools(phishing_tools)

    def agent(state: PhishingAnalysisState) -> dict:
        system_msg = SystemMessage(
            content=f"{PHISHING_SYSTEM_PROMPT}\n\n현재 분석 대상 URL: {state['url']}"
        )

        msg_count = len(state["messages"])
        print(f"\n{'='*50}")
        print(f"🤖 [PHISHING AGENT] LLM 호출 (누적 메시지: {msg_count}개)")
        print(f"{'='*50}")

        response = llm_with_tools.invoke([system_msg] + state["messages"])

        if response.tool_calls:
            for tc in response.tool_calls:
                args_preview = str(tc["args"])[:100]
                print(f"🔧 [PHISHING AGENT] Tool 호출: {tc['name']}({args_preview})")
        else:
            print(f"💬 [PHISHING AGENT] 텍스트 응답 (종료)")

        update: dict = {"messages": [response]}

        for tc in response.tool_calls:
            if tc["name"] == "phishing_verdict":
                args = tc["args"]
                update["category"] = args.get("category")
                update["confidence"] = args.get("confidence")
                update["evidence_summary"] = args.get("evidence_summary")

        return update

    tool_node = ToolNode(phishing_tools)

    builder = StateGraph(PhishingAnalysisState)
    builder.add_node("agent", agent)
    builder.add_node("tools", tool_node)

    builder.add_edge(START, "agent")
    builder.add_conditional_edges("agent", tools_condition)
    builder.add_edge("tools", "agent")

    return builder.compile()