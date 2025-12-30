#!/usr/bin/env python3
"""Analyze why batch of 30 jobs was not fully completed (only 18 processed)."""

from database.client import db
from datetime import datetime, timedelta

print("=== BATCH COMPLETION ANALYSIS ===\n")

# Define time window for recent enrichments (last 30 minutes)
cutoff = datetime.utcnow() - timedelta(minutes=30)
cutoff_str = cutoff.isoformat()

print(f"Analyzing enrichments since: {cutoff_str}")

# Get all enrichments in last 30 minutes
recent_enrichments = db.client.table("llm_enrichment")\
    .select("job_posting_id, enrichment_completed_at, enrichment_error, created_at")\
    .gte("enrichment_completed_at", cutoff_str)\
    .order("enrichment_completed_at", desc=False)\
    .execute()

completed_count = len(recent_enrichments.data)
print(f"\n✅ Completed enrichments in last 30 min: {completed_count}")

# Get failed enrichments (with errors) in last 30 minutes
failed_enrichments = db.client.table("llm_enrichment")\
    .select("job_posting_id, enrichment_error, created_at")\
    .not_.is_("enrichment_error", "null")\
    .gte("created_at", cutoff_str)\
    .execute()

failed_count = len(failed_enrichments.data)
print(f"❌ Failed enrichments in last 30 min: {failed_count}")

# Get enrichments that started but didn't complete
incomplete = db.client.table("llm_enrichment")\
    .select("job_posting_id, enrichment_error, created_at, enrichment_completed_at")\
    .is_("enrichment_completed_at", "null")\
    .is_("enrichment_error", "null")\
    .gte("created_at", cutoff_str)\
    .execute()

incomplete_count = len(incomplete.data)
print(f"⏳ Incomplete enrichments (started but not finished): {incomplete_count}")

total_attempted = completed_count + failed_count + incomplete_count
print(f"\n📊 Total enrichment attempts: {total_attempted}")
print(f"   Success rate: {(completed_count/total_attempted*100) if total_attempted > 0 else 0:.1f}%")

# Show timeline of enrichments
if recent_enrichments.data:
    print(f"\n=== ENRICHMENT TIMELINE (last 30 min) ===")
    for i, e in enumerate(recent_enrichments.data, 1):
        completed = e.get("enrichment_completed_at")
        if completed:
            dt = datetime.fromisoformat(completed.replace('Z', '+00:00'))
            time_str = dt.strftime("%H:%M:%S")
            print(f"{i}. {time_str}")
    
    # Calculate time gaps
    if len(recent_enrichments.data) >= 2:
        first = datetime.fromisoformat(recent_enrichments.data[0]["enrichment_completed_at"].replace('Z', '+00:00'))
        last = datetime.fromisoformat(recent_enrichments.data[-1]["enrichment_completed_at"].replace('Z', '+00:00'))
        duration = (last - first).total_seconds()
        avg_time = duration / len(recent_enrichments.data) if len(recent_enrichments.data) > 1 else 0
        
        print(f"\n⏱️  Duration: {duration:.0f} seconds ({duration/60:.1f} minutes)")
        print(f"⏱️  Average time per job: {avg_time:.1f} seconds")
        print(f"⏱️  Expected batch of 30: {30 * avg_time / 60:.1f} minutes")

# Show failed enrichments details
if failed_enrichments.data:
    print(f"\n=== FAILED ENRICHMENTS ===")
    for e in failed_enrichments.data[:5]:
        job_id = e.get("job_posting_id")
        error = e.get("enrichment_error", "")
        
        # Get job title
        job = db.client.table("job_postings")\
            .select("title")\
            .eq("id", job_id)\
            .maybe_single()\
            .execute()
        
        title = job.data.get("title", "N/A") if job.data else "N/A"
        print(f"  - {title[:60]}")
        print(f"    Error: {error[:150]}")

# Show incomplete enrichments
if incomplete.data:
    print(f"\n=== INCOMPLETE ENRICHMENTS (stuck?) ===")
    for e in incomplete.data[:5]:
        job_id = e.get("job_posting_id")
        created = e.get("created_at")
        
        # Get job title
        job = db.client.table("job_postings")\
            .select("title")\
            .eq("id", job_id)\
            .maybe_single()\
            .execute()
        
        title = job.data.get("title", "N/A") if job.data else "N/A"
        
        if created:
            created_dt = datetime.fromisoformat(created.replace('Z', '+00:00'))
            age = datetime.utcnow() - created_dt.replace(tzinfo=None)
            print(f"  - {title[:60]}")
            print(f"    Started: {age.total_seconds()/60:.1f} minutes ago")

print(f"\n=== DIAGNOSIS ===")
if completed_count < 30 and failed_count > 0:
    print(f"🔍 Batch incomplete due to {failed_count} failures")
    print("   Check error messages above for root cause")
elif completed_count < 30 and incomplete_count > 0:
    print(f"🔍 Batch incomplete - {incomplete_count} jobs stuck/in-progress")
    print("   Service may have crashed or restarted mid-batch")
elif completed_count < 30:
    print(f"🔍 Only {completed_count} jobs processed - possible causes:")
    print("   1. Service restarted mid-batch")
    print("   2. Fewer than 30 jobs were pending at that time")
    print("   3. Rate limiting kicked in")
else:
    print("✅ Batch processing appears normal")

print(f"\n=== RECOMMENDATIONS ===")
if failed_count > 5:
    print("1. High failure rate - investigate error patterns")
    print("2. May need to add error handling/retry logic")
elif incomplete_count > 5:
    print("1. Jobs getting stuck - check service stability")
    print("2. Consider adding timeout mechanism")
elif avg_time > 10:
    print("1. Enrichment taking too long (>10s per job)")
    print("2. Consider optimizing LLM calls or reducing delay")
else:
    print("1. System appears healthy")
    print("2. Continue monitoring for patterns")
