"""Check how many companies have size_category filled."""

from database import db

print("="*80)
print("SIZE CATEGORY COVERAGE CHECK")
print("="*80)

# Total companies
total = db.client.table("company_master_data")\
    .select("id", count="exact")\
    .execute()

print(f"\nTotal companies: {total.count}")

# Companies with size_category
with_size = db.client.table("company_master_data")\
    .select("id", count="exact")\
    .not_.is_("size_category", "null")\
    .execute()

print(f"Companies with size_category: {with_size.count}")
print(f"Coverage: {(with_size.count / total.count * 100):.1f}%")

# Companies with size_enriched_at
enriched = db.client.table("company_master_data")\
    .select("id", count="exact")\
    .not_.is_("size_enriched_at", "null")\
    .execute()

print(f"\nCompanies with size_enriched_at: {enriched.count}")

# Breakdown by size_category
print("\nBreakdown by size_category:")
categories = ['startup', 'scaleup', 'sme', 'established_enterprise', 'corporate', 'public_company', 'government', 'unknown']

for cat in categories:
    count = db.client.table("company_master_data")\
        .select("id", count="exact")\
        .eq("size_category", cat)\
        .execute()
    if count.count > 0:
        print(f"  {cat}: {count.count}")

# Check if there are enrichment errors
errors = db.client.table("company_master_data")\
    .select("id", count="exact")\
    .not_.is_("size_enrichment_error", "null")\
    .execute()

print(f"\nCompanies with enrichment errors: {errors.count}")

if errors.count > 0:
    # Get some examples
    error_examples = db.client.table("company_master_data")\
        .select("name, size_enrichment_error")\
        .not_.is_("size_enrichment_error", "null")\
        .limit(5)\
        .execute()
    
    print("\nExample errors:")
    for e in error_examples.data:
        print(f"  {e['name']}: {e['size_enrichment_error'][:100]}...")

print("\n" + "="*80)
