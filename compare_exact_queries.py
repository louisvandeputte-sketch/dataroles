"""Compare the exact queries to find the discrepancy."""

from database import db

print("="*80)
print("EXACT QUERY COMPARISON")
print("="*80)

# STATS QUERY (from /api/jobs/enrich/stats endpoint)
print("\n1. STATS ENDPOINT QUERY:")
print("   db.client.table('llm_enrichment')")
print("   .select('id, job_postings!inner(title_classification)', count='exact')")
print("   .eq('job_postings.title_classification', 'Data')")
print("   .not_.is_('enrichment_completed_at', 'null')")

stats_result = db.client.table("llm_enrichment")\
    .select("id, job_postings!inner(title_classification)", count="exact")\
    .eq("job_postings.title_classification", "Data")\
    .not_.is_("enrichment_completed_at", "null")\
    .execute()

print(f"\n   COUNT: {stats_result.count}")
print(f"   RECORDS RETURNED: {len(stats_result.data)}")

# FILTER QUERY (from database/client.py with our server-side filter)
print("\n2. FILTER QUERY (server-side):")
print("   db.client.table('job_postings')")
print("   .select('*, llm_enrichment(...)', count='exact')")
print("   .eq('title_classification', 'Data')")
print("   .not_.is_('llm_enrichment.enrichment_completed_at', 'null')")

filter_result = db.client.table("job_postings")\
    .select("id, title, llm_enrichment(enrichment_completed_at)", count="exact")\
    .eq("title_classification", "Data")\
    .not_.is_("llm_enrichment.enrichment_completed_at", "null")\
    .execute()

print(f"\n   COUNT: {filter_result.count}")
print(f"   RECORDS RETURNED: {len(filter_result.data)}")

# THE KEY INSIGHT
print("\n" + "="*80)
print("THE PROBLEM:")
print("="*80)
print(f"Stats query: {stats_result.count} (counts llm_enrichment records)")
print(f"Filter query: {filter_result.count} (counts job_postings records)")
print(f"Difference: {filter_result.count - stats_result.count}")

# Check: Are there jobs with multiple enrichment records?
print("\n3. CHECKING FOR DUPLICATE ENRICHMENTS:")
all_enrichments = db.client.table("llm_enrichment")\
    .select("job_posting_id, enrichment_completed_at, job_postings!inner(title_classification)")\
    .eq("job_postings.title_classification", "Data")\
    .not_.is_("enrichment_completed_at", "null")\
    .execute()

from collections import Counter
job_counts = Counter(e['job_posting_id'] for e in all_enrichments.data)
duplicates = {job_id: count for job_id, count in job_counts.items() if count > 1}

print(f"   Total enrichment records: {len(all_enrichments.data)}")
print(f"   Unique jobs: {len(job_counts)}")
print(f"   Jobs with multiple enrichments: {len(duplicates)}")

if duplicates:
    print("\n   Jobs with multiple completed enrichments:")
    for job_id, count in sorted(duplicates.items(), key=lambda x: x[1], reverse=True)[:5]:
        job = db.client.table("job_postings")\
            .select("title")\
            .eq("id", job_id)\
            .single()\
            .execute()
        print(f"     - {job.data['title']}: {count} enrichments")

# SOLUTION
print("\n" + "="*80)
print("SOLUTION:")
print("="*80)
print("The stats endpoint should count DISTINCT job_posting_id, not enrichment records!")
print("Current: SELECT COUNT(*) FROM llm_enrichment WHERE...")
print("Should be: SELECT COUNT(DISTINCT job_posting_id) FROM llm_enrichment WHERE...")
print("="*80)
