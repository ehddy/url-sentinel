"""
설정값 모음
.env에서 읽어오되, 기본값도 제공합니다.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# AWS Bedrock
BEDROCK_MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "us.anthropic.claude-sonnet-4-20250514")
AWS_REGION = os.getenv("AWS_DEFAULT_REGION", "us-east-1")

# 브라우저 헤드리스 설정 (로컬: false, Docker: true)
CRAWL4AI_HEADLESS = os.getenv("CRAWL4AI_HEADLESS", "false").lower() == "true"

# Google Custom Search API
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
GOOGLE_CX = os.getenv("GOOGLE_CX", "")
GOOGLE_SEARCH_DAYS = int(os.getenv("GOOGLE_SEARCH_DAYS", "30"))