#!/usr/bin/env python3
"""Test enrichment with raw output logging."""

import json
from openai import OpenAI
from config.settings import settings

client = OpenAI(api_key=settings.openai_api_key, timeout=300.0)

COMPANY_ENRICHMENT_PROMPT_ID = "pmpt_68fd06175d7c8190bd8767fddcb5486a0e87d16aa5f38bc2"
COMPANY_ENRICHMENT_PROMPT_VERSION = "12"

# Test with a simple company
company_info = "Company Name: Deliverect\nWebsite: https://www.deliverect.com"

print("Testing enrichment with prompt v12...")
print(f"Input: {company_info}")
print("=" * 80)

response = client.responses.create(
    prompt={
        "id": COMPANY_ENRICHMENT_PROMPT_ID,
        "version": COMPANY_ENRICHMENT_PROMPT_VERSION
    },
    input=company_info
)

print("\nRaw Response:")
print(response)
print("\n" + "=" * 80)

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
    print("\nParsed Enrichment Data:")
    print(json.dumps(enrichment_data, indent=2, ensure_ascii=False))
    
    print("\n" + "=" * 80)
    print("Field Check:")
    print(f"  - category_en: {enrichment_data.get('category_en')}")
    print(f"  - category_nl: {enrichment_data.get('category_nl')}")
    print(f"  - category_fr: {enrichment_data.get('category_fr')}")
    print(f"  - confidence: {enrichment_data.get('confidence')}")
    print(f"  - weetjes: {enrichment_data.get('weetjes')}")
    print(f"  - sector_en: {enrichment_data.get('sector_en')}")
    print(f"  - aantal_werknemers: {enrichment_data.get('aantal_werknemers')}")
else:
    print("\n❌ Could not extract enrichment data")
