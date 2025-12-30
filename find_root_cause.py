"""Find the root cause of the discrepancy."""

from database import db

print("="*80)
print("ROOT CAUSE ANALYSIS")
print("="*80)

# The key insight: Stats query uses INNER JOIN, Filter query uses LEFT JOIN
# Let's check if there are jobs with NO enrichment vs MULTIPLE enrichments

print("\n1. Total Data jobs:")
total_data = db.client.table("job_postings")\
    .select("id", count="exact")\
    .eq("title_classification", "Data")\
    .execute()
print(f"   {total_data.count} Data jobs")

print("\n2. Stats query (FROM llm_enrichment with INNER JOIN):")
print("   This counts enrichment RECORDS where job has title_classification='Data'")
stats_query = db.client.table("llm_enrichment")\
    .select("id, job_posting_id, job_postings!inner(title_classification)", count="exact")\
    .eq("job_postings.title_classification", "Data")\
    .not_.is_("enrichment_completed_at", "null")\
    .execute()
print(f"   {stats_query.count} enrichment records")

print("\n3. Filter query (FROM job_postings with LEFT JOIN):")
print("   This counts JOBS where title_classification='Data' AND has enrichment")
filter_query = db.client.table("job_postings")\
    .select("id, llm_enrichment(enrichment_completed_at)", count="exact")\
    .eq("title_classification", "Data")\
    .not_.is_("llm_enrichment.enrichment_completed_at", "null")\
    .execute()
print(f"   {filter_query.count} jobs with enrichment")

print("\n4. THE PROBLEM:")
print(f"   Stats counts ENRICHMENT RECORDS: {stats_query.count}")
print(f"   Filter counts UNIQUE JOBS: {filter_query.count}")
print(f"   If a job has multiple enrichment records, stats counts it multiple times!")

# Check: How many jobs have multiple completed enrichments?
print("\n5. Checking for jobs with multiple COMPLETED enrichments...")

# Get all completed enrichments for Data jobs
all_completed = db.client.table("llm_enrichment")\
    .select("job_posting_id, id, enrichment_completed_at, job_postings!inner(title_classification)")\
    .eq("job_postings.title_classification", "Data")\
    .not_.is_("enrichment_completed_at", "null")\
    .execute()

from collections import Counter
job_counts = Counter(e['job_posting_id'] for e in all_completed.data)
duplicates = [(job_id, count) for job_id, count in job_counts.items() if count > 1]

print(f"   Jobs with multiple completed enrichments: {len(duplicates)}")
print(f"   Total duplicate records: {sum(count - 1 for _, count in duplicates)}")

if duplicates:
    print("\n   Top 10 jobs with most completed enrichments:")
    for job_id, count in sorted(duplicates, key=lambda x: x[1], reverse=True)[:10]:
        job = db.client.table("job_postings")\
            .select("title")\
            .eq("id", job_id)\
            .single()\
            .execute()
        print(f"     - {job.data['title']}: {count} completed enrichments")

print("\n" + "="*80)
print("CONCLUSION:")
print("="*80)
print("The stats query counts ENRICHMENT RECORDS (can have duplicates)")
print("The filter query counts UNIQUE JOBS (no duplicates)")
print(f"Difference: {stats_query.count} - {filter_query.count} = {stats_query.count - filter_query.count}")
print("\nThe stats query should count UNIQUE jobs, not enrichment records!")
print("="*80)
