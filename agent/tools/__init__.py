from agent.tools.dns_check import dns_check
from agent.tools.crawl import crawl_page
from agent.tools.whois_lookup import whois_lookup
from agent.tools.google_search import google_search
from agent.tools.screenshot import capture_and_analyze
from agent.tools.verdict import make_verdict

# 에이전트에 바인딩할 전체 Tool 리스트
all_tools = [
    dns_check,
    crawl_page,
    whois_lookup,
    google_search,
    capture_and_analyze,
    make_verdict,
]

__all__ = [
    "all_tools",
    "dns_check",
    "crawl_page",
    "whois_lookup",
    "google_search",
    "capture_and_analyze",
    "make_verdict",
]