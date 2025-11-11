#!/usr/bin/env python3
"""Test prompt version 14 with a sample company."""

import json
from openai import OpenAI
from config.settings import settings

client = OpenAI(api_key=settings.openai_api_key, timeout=300.0)

COMPANY_ENRICHMENT_PROMPT_ID = "pmpt_68fd06175d7c8190bd8767fddcb5486a0e87d16aa5f38bc2"
COMPANY_ENRICHMENT_PROMPT_VERSION = "14"

# Test with a Belgian company
company_info = "Company Name: Showpad\nWebsite: https://www.showpad.com"

print("Testing enrichment with prompt v14...")
print(f"Input: {company_info}")
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
    print("\n✅ Prompt v14 Response:")
    print("=" * 80)
    
    # Check key fields
    print(f"\n📊 Basic Info:")
    print(f"  - Website: {enrichment_data.get('website') or enrichment_data.get('bedrijfswebsite')}")
    print(f"  - Careers: {enrichment_data.get('careers_page') or enrichment_data.get('jobspagina')}")
    print(f"  - Employees: {enrichment_data.get('employee_count_range') or enrichment_data.get('aantal_werknemers')}")
    
    print(f"\n🏢 Sector (should be 1-3 words):")
    print(f"  - EN: {enrichment_data.get('sector_en')}")
    print(f"  - NL: {enrichment_data.get('sector_nl')}")
    print(f"  - FR: {enrichment_data.get('sector_fr')}")
    
    # Check maturity structure
    maturity = enrichment_data.get("maturity", {})
    category_obj = enrichment_data.get("category", {})
    
    print(f"\n📈 Maturity Classification:")
    if maturity:
        print(f"  - Structure: nested in 'maturity'")
        print(f"  - Category EN: {maturity.get('category_en')}")
        print(f"  - Category NL: {maturity.get('category_nl')}")
        print(f"  - Category FR: {maturity.get('category_fr')}")
        print(f"  - Confidence: {maturity.get('confidence')}")
    elif category_obj:
        print(f"  - Structure: nested in 'category' object")
        print(f"  - Category EN: {category_obj.get('en')}")
        print(f"  - Category NL: {category_obj.get('nl')}")
        print(f"  - Category FR: {category_obj.get('fr')}")
        print(f"  - Confidence: {enrichment_data.get('confidence')}")
    else:
        print(f"  - Structure: flat (top-level)")
        print(f"  - Category EN: {enrichment_data.get('category_en')}")
        print(f"  - Category NL: {enrichment_data.get('category_nl')}")
        print(f"  - Category FR: {enrichment_data.get('category_fr')}")
        print(f"  - Confidence: {enrichment_data.get('confidence')}")
    
    # Check factlets
    factlets = enrichment_data.get('factlets') or enrichment_data.get('weetjes')
    print(f"\n💡 Factlets:")
    if factlets:
        print(f"  - Count: {len(factlets)}")
        for i, f in enumerate(factlets, 1):
            print(f"  {i}. {f.get('category')}: {f.get('text_en', '')[:60]}...")
            if i == 1 and 'funding' in f.get('category', '').lower():
                print(f"     ✅ Funding factlet is first (as required)")
    else:
        print(f"  - None found")
    
    print("\n" + "=" * 80)
    print("Full JSON structure:")
    print(json.dumps(enrichment_data, indent=2, ensure_ascii=False)[:2000] + "...")
else:
    print("\n❌ Could not extract enrichment data")
