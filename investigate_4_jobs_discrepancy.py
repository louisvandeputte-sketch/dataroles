"""Investigate the 4 jobs discrepancy between filter and stats."""

from database import db

print("="*80)
print("INVESTIGATING 4 JOBS DISCREPANCY")
print("="*80)

# Query 1: How stats calculates enriched jobs (from /api/jobs/enrich/stats)
print("\n1. STATS QUERY (2123 enriched):")
print("   Counts: llm_enrichment WHERE job_postings.title_classification='Data' AND enrichment_completed_at IS NOT NULL")

enriched_stats = db.client.table("llm_enrichment")\
    .select("id, job_posting_id, enrichment_completed_at, job_postings!inner(id, title, title_classification)", count="exact")\
    .eq("job_postings.title_classification", "Data")\
    .not_.is_("enrichment_completed_at", "null")\
    .execute()

print(f"   Result: {enriched_stats.count} enriched Data jobs")

# Query 2: How filter calculates enriched jobs (from database/client.py search_jobs)
print("\n2. FILTER QUERY (2127 enriched):")
print("   Counts: job_postings WHERE title_classification='Data' AND llm_enrichment.enrichment_completed_at IS NOT NULL")

enriched_filter = db.client.table("job_postings")\
    .select("id, title, title_classification, llm_enrichment(enrichment_completed_at)", count="exact")\
    .eq("title_classification", "Data")\
    .not_.is_("llm_enrichment.enrichment_completed_at", "null")\
    .execute()

print(f"   Result: {enriched_filter.count} enriched Data jobs")

# Find the difference
print(f"\n3. DIFFERENCE: {enriched_filter.count} - {enriched_stats.count} = {enriched_filter.count - enriched_stats.count} jobs")

# Get IDs from both queries
stats_ids = {e['job_posting_id'] for e in enriched_stats.data}
filter_ids = {j['id'] for j in enriched_filter.data}

# Find jobs that are in filter but not in stats
only_in_filter = filter_ids - stats_ids
only_in_stats = stats_ids - filter_ids

print(f"\n4. JOBS ONLY IN FILTER (not in stats): {len(only_in_filter)}")
if only_in_filter:
    for job_id in list(only_in_filter)[:10]:
        job = db.client.table("job_postings")\
            .select("id, title, title_classification")\
            .eq("id", job_id)\
            .single()\
            .execute()
        
        enrichment = db.client.table("llm_enrichment")\
            .select("*")\
            .eq("job_posting_id", job_id)\
            .execute()
        
        print(f"\n   Job: {job.data['title']}")
        print(f"   ID: {job_id}")
        print(f"   title_classification: {job.data['title_classification']}")
        print(f"   Enrichment records: {len(enrichment.data)}")
        if enrichment.data:
            for e in enrichment.data:
                print(f"     - completed_at: {e.get('enrichment_completed_at')}")
                print(f"     - created_at: {e.get('created_at')}")

print(f"\n5. JOBS ONLY IN STATS (not in filter): {len(only_in_stats)}")
if only_in_stats:
    for job_id in list(only_in_stats)[:10]:
        # Get enrichment record
        enrichment = db.client.table("llm_enrichment")\
            .select("*, job_postings(id, title, title_classification)")\
            .eq("job_posting_id", job_id)\
            .single()\
            .execute()
        
        print(f"\n   Job: {enrichment.data.get('job_postings', {}).get('title', 'Unknown')}")
        print(f"   ID: {job_id}")
        print(f"   title_classification: {enrichment.data.get('job_postings', {}).get('title_classification')}")
        print(f"   completed_at: {enrichment.data.get('enrichment_completed_at')}")

print("\n" + "="*80)
print("ANALYSIS COMPLETE")
print("="*80)
