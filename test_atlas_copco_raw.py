#!/usr/bin/env python3
"""Test Atlas Copco enrichment to see raw API response."""

import json
from openai import OpenAI
from config.settings import settings

client = OpenAI(api_key=settings.openai_api_key, timeout=300.0)

COMPANY_ENRICHMENT_PROMPT_ID = "pmpt_68fd06175d7c8190bd8767fddcb5486a0e87d16aa5f38bc2"
COMPANY_ENRICHMENT_PROMPT_VERSION = "14"

company_info = "Company Name: Atlas Copco Group"

print("Testing Atlas Copco enrichment with prompt v14...")
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
    print("\n✅ API Response received")
    print("=" * 80)
    
    # Check maturity fields
    print("\n📊 Maturity Fields in Response:")
    print(f"  - maturity_en: {enrichment_data.get('maturity_en')}")
    print(f"  - maturity_nl: {enrichment_data.get('maturity_nl')}")
    print(f"  - maturity_fr: {enrichment_data.get('maturity_fr')}")
    print(f"  - category_en: {enrichment_data.get('category_en')}")
    print(f"  - confidence: {enrichment_data.get('confidence')}")
    print(f"  - key_arguments_en: {enrichment_data.get('key_arguments_en')}")
    print(f"  - key_arguments: {enrichment_data.get('key_arguments')}")
    print(f"  - sources: {enrichment_data.get('sources')}")
    
    # Check nested structures
    maturity = enrichment_data.get('maturity', {})
    category_obj = enrichment_data.get('category', {})
    
    if maturity:
        print(f"\n  Nested 'maturity' object found:")
        print(f"    {json.dumps(maturity, indent=4)}")
    
    if category_obj:
        print(f"\n  Nested 'category' object found:")
        print(f"    {json.dumps(category_obj, indent=4)}")
    
    print("\n" + "=" * 80)
    print("Full JSON (first 3000 chars):")
    print(json.dumps(enrichment_data, indent=2, ensure_ascii=False)[:3000])
else:
    print("\n❌ Could not extract enrichment data")
