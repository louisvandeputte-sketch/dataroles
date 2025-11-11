#!/usr/bin/env python3
"""Test prompt version 14 - show full JSON output."""

import json
from openai import OpenAI
from config.settings import settings

client = OpenAI(api_key=settings.openai_api_key, timeout=300.0)

COMPANY_ENRICHMENT_PROMPT_ID = "pmpt_68fd06175d7c8190bd8767fddcb5486a0e87d16aa5f38bc2"
COMPANY_ENRICHMENT_PROMPT_VERSION = "14"

# Test with a simple company
company_info = "Company Name: Showpad"

print("Testing prompt v14 - Full JSON output")
print("=" * 80)

response = client.responses.create(
    prompt={
        "id": COMPANY_ENRICHMENT_PROMPT_ID,
        "version": COMPANY_ENRICHMENT_PROMPT_VERSION
    },
    input=company_info
)

# Extract structured output
enrichment_data = None
if hasattr(response, 'output') and response.output:
    for item in response.output:
        if hasattr(item, 'type') and item.type == 'message' and hasattr(item, 'content'):
            for content in item.content:
                if hasattr(content, 'type') and content.type == 'output_text':
                    enrichment_data = json.loads(content.text)
                    break
        if enrichment_data:
            break

if enrichment_data:
    print("\nFull JSON Output:")
    print(json.dumps(enrichment_data, indent=2, ensure_ascii=False))
else:
    print("❌ Could not extract data")
