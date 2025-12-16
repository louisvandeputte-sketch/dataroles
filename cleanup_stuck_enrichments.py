#!/usr/bin/env python3
"""Clean up stuck enrichment records that are blocking new enrichment attempts."""

from database.client import db
from datetime import datetime, timedelta

print("=== CLEANING UP STUCK ENRICHMENT RECORDS ===\n")

# Define cutoff: 1 hour ago
cutoff = datetime.utcnow() - timedelta(hours=1)
cutoff_str = cutoff.isoformat()

print(f"Cutoff time: {cutoff_str}")
print("Looking for enrichment records that are:")
print("  - Created more than 1 hour ago")
print("  - enrichment_completed_at IS NULL")
print("  - enrichment_error IS NULL")
print()

# Find stuck enrichment records
stuck = db.client.table("llm_enrichment")\
    .select("id, job_posting_id, created_at, job_postings!inner(title, title_classification)")\
    .eq("job_postings.title_classification", "Data")\
    .is_("enrichment_completed_at", "null")\
    .is_("enrichment_error", "null")\
    .lt("created_at", cutoff_str)\
    .execute()

print(f"Found {len(stuck.data)} stuck enrichment records\n")

if not stuck.data:
    print("✅ No stuck enrichments found!")
    exit(0)

# Show sample
print("Sample of stuck enrichments (first 10):")
for i, e in enumerate(stuck.data[:10], 1):
    created = e.get("created_at")
    job_title = e.get("job_postings", {}).get("title", "N/A")
    
    if created:
        created_dt = datetime.fromisoformat(created.replace('Z', '+00:00'))
        age = datetime.utcnow() - created_dt.replace(tzinfo=None)
        hours = age.total_seconds() / 3600
        print(f"{i}. {job_title[:60]} - stuck for {hours:.1f} hours")

# Ask for confirmation
print(f"\n⚠️  About to DELETE {len(stuck.data)} stuck enrichment records")
print("This will allow these jobs to be re-enriched.")
print()

response = input("Continue? (yes/no): ")

if response.lower() != 'yes':
    print("Aborted.")
    exit(0)

# Delete stuck records
print(f"\nDeleting {len(stuck.data)} records...")

deleted_count = 0
for e in stuck.data:
    enrichment_id = e.get("id")
    
    try:
        db.client.table("llm_enrichment")\
            .delete()\
            .eq("id", enrichment_id)\
            .execute()
        
        deleted_count += 1
        
        if deleted_count % 10 == 0:
            print(f"  Deleted {deleted_count}/{len(stuck.data)}...")
    
    except Exception as ex:
        print(f"  Error deleting {enrichment_id}: {ex}")

print(f"\n✅ Deleted {deleted_count} stuck enrichment records")

# Verify
print("\nVerifying cleanup...")
remaining = db.client.table("llm_enrichment")\
    .select("id", count="exact")\
    .is_("enrichment_completed_at", "null")\
    .is_("enrichment_error", "null")\
    .lt("created_at", cutoff_str)\
    .execute()

print(f"Remaining stuck records: {remaining.count}")

if remaining.count == 0:
    print("✅ All stuck enrichments cleaned up!")
else:
    print(f"⚠️  {remaining.count} stuck records remain")

print("\n=== IMPACT ===")
print(f"These {deleted_count} jobs can now be re-enriched by the auto-enrichment service.")
print("The service will pick them up in the next cycle (within 1 minute).")
