#!/usr/bin/env python3
"""Check if job enrichment has stalled and diagnose the issue."""

from database.client import db
from datetime import datetime, timedelta

print("=== JOB ENRICHMENT STALL DIAGNOSIS ===\n")

# Check total pending
all_data = db.client.table("job_postings")\
    .select("id", count="exact")\
    .eq("title_classification", "Data")\
    .eq("is_active", True)\
    .execute()

enriched = db.client.table("llm_enrichment")\
    .select("job_posting_id", count="exact")\
    .eq("job_postings.title_classification", "Data")\
    .eq("job_postings.is_active", True)\
    .not_.is_("enrichment_completed_at", "null")\
    .execute()

pending = all_data.count - enriched.count

print(f"Total active Data jobs: {all_data.count}")
print(f"Enriched: {enriched.count}")
print(f"Pending: {pending}")

# Check recent enrichment activity
print(f"\n=== RECENT ENRICHMENT ACTIVITY ===")

# Get last 10 enrichments
recent = db.client.table("llm_enrichment")\
    .select("job_posting_id, enrichment_completed_at, job_postings!inner(title)")\
    .not_.is_("enrichment_completed_at", "null")\
    .order("enrichment_completed_at", desc=True)\
    .limit(10)\
    .execute()

if recent.data:
    print("Last 10 enrichments:")
    for i, e in enumerate(recent.data, 1):
        completed = e.get("enrichment_completed_at")
        title = e.get("job_postings", {}).get("title", "N/A")
        
        if completed:
            completed_dt = datetime.fromisoformat(completed.replace('Z', '+00:00'))
            age = datetime.now(completed_dt.tzinfo) - completed_dt
            hours = age.total_seconds() / 3600
            
            print(f"{i}. {title[:50]} - {hours:.1f}h ago")
    
    # Check if enrichment is stalled
    last_enrichment = recent.data[0].get("enrichment_completed_at")
    if last_enrichment:
        last_dt = datetime.fromisoformat(last_enrichment.replace('Z', '+00:00'))
        time_since_last = datetime.now(last_dt.tzinfo) - last_dt
        hours_since = time_since_last.total_seconds() / 3600
        
        print(f"\n⏰ Last enrichment: {hours_since:.1f} hours ago")
        
        if hours_since > 1:
            print("⚠️ WARNING: No enrichments in over 1 hour - service may be stalled!")
        elif hours_since > 0.5:
            print("⚠️ CAUTION: No enrichments in 30+ minutes - check service status")
        else:
            print("✅ Service appears to be running (recent activity)")
else:
    print("❌ No enrichment records found!")

# Check for jobs with errors
print(f"\n=== ENRICHMENT ERRORS ===")
errors = db.client.table("llm_enrichment")\
    .select("job_posting_id, enrichment_error, job_postings!inner(title)")\
    .not_.is_("enrichment_error", "null")\
    .order("updated_at", desc=True)\
    .limit(5)\
    .execute()

if errors.data:
    print(f"Found {len(errors.data)} recent errors:")
    for e in errors.data:
        title = e.get("job_postings", {}).get("title", "N/A")
        error = e.get("enrichment_error", "")
        print(f"  - {title[:50]}")
        print(f"    Error: {error[:100]}")
else:
    print("No recent errors found")

print(f"\n=== POSSIBLE CAUSES ===")
print("1. Railway deployment failed or service crashed")
print("2. DISABLE_AUTO_ENRICHMENT env var is set to true")
print("3. OpenAI API rate limit or quota exceeded")
print("4. Database connection issues")
print("5. Code deployed but service not restarted")
print("\nCheck Railway logs for more details")
