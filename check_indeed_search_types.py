#!/usr/bin/env python3
"""Check Indeed jobs and their search query relationship."""

from database.client import db

print("Checking Indeed Jobs Search Types")
print("=" * 80)

# 1. Get Indeed jobs
indeed_jobs = db.client.table("job_postings")\
    .select("id, title, source")\
    .eq("source", "indeed")\
    .limit(5)\
    .execute()

print(f"\n1. Sample Indeed Jobs:")
for job in indeed_jobs.data:
    # Check scrape history
    history = db.client.table("job_scrape_history")\
        .select("scrape_run_id")\
        .eq("job_posting_id", job['id'])\
        .execute()
    
    if history.data:
        run_id = history.data[0]['scrape_run_id']
        
        # Get scrape run
        run = db.client.table("scrape_runs")\
            .select("search_query_id")\
            .eq("id", run_id)\
            .execute()
        
        if run.data and run.data[0].get('search_query_id'):
            query_id = run.data[0]['search_query_id']
            
            # Get search query
            query = db.client.table("search_queries")\
                .select("search_query, job_type_id")\
                .eq("id", query_id)\
                .execute()
            
            if query.data:
                print(f"\n  Job: {job['title'][:50]}")
                print(f"    Search Query: {query.data[0]['search_query']}")
                print(f"    Job Type ID: {query.data[0].get('job_type_id')}")
                
                # Check if job has type assignment
                types = db.client.table("job_type_assignments")\
                    .select("job_types(name)")\
                    .eq("job_posting_id", job['id'])\
                    .execute()
                
                type_names = [t['job_types']['name'] for t in types.data if t.get('job_types')]
                print(f"    Assigned Types: {type_names or 'NONE'}")

# 2. Check if search queries have job_type_id
print(f"\n2. Indeed Search Queries:")
queries = db.client.table("search_queries")\
    .select("id, search_query, job_type_id, source")\
    .eq("source", "indeed")\
    .execute()

for query in queries.data:
    print(f"  {query['search_query']:30} | job_type_id: {query.get('job_type_id') or 'NULL'}")

print("\n" + "=" * 80)
