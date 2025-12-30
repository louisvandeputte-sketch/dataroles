"""Find jobs without LLM enrichment."""

from database import db

# Find jobs without enrichment by checking if job_posting_id exists in llm_enrichment
all_jobs = db.client.table('job_postings')\
    .select('id, title, company_id, posted_date_corrected, created_at')\
    .eq('is_active', True)\
    .order('created_at', desc=True)\
    .limit(1000)\
    .execute()

print(f"Checking {len(all_jobs.data)} active jobs...")

# Get all enriched job IDs
enriched = db.client.table('llm_enrichment')\
    .select('job_posting_id')\
    .execute()

enriched_ids = {e['job_posting_id'] for e in enriched.data}
print(f"Found {len(enriched_ids)} enriched jobs")

# Find unenriched
unenriched = [job for job in all_jobs.data if job['id'] not in enriched_ids]

print(f"\n{'='*80}")
print(f"Found {len(unenriched)} UNENRICHED jobs:")
print(f"{'='*80}\n")

# Get company names for unenriched jobs
for job in unenriched[:20]:
    company = db.client.table('companies')\
        .select('name')\
        .eq('id', job['company_id'])\
        .single()\
        .execute()
    
    company_name = company.data['name'] if company.data else 'Unknown'
    
    print(f"ID: {job['id']}")
    print(f"Title: {job['title']}")
    print(f"Company: {company_name}")
    print(f"Posted: {job.get('posted_date_corrected', 'N/A')}")
    print(f"Created: {job.get('created_at', 'N/A')}")
    print('-' * 80)
