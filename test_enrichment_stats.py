#!/usr/bin/env python3
"""Test the new enrichment stats calculation."""

from database.client import db

print("=== NEW ENRICHMENT STATS CALCULATION ===\n")

# Step 1: Total 'Data' jobs (title_classification = 'Data', excludes NIS from title check)
total_result = db.client.table("job_postings")\
    .select("id", count="exact")\
    .eq("title_classification", "Data")\
    .execute()
total = total_result.count or 0

print(f"Step 1 - Total Data jobs (title_classification='Data'): {total}")

# Step 2: Enriched jobs = all jobs with title_classification='Data' that have completed enrichment
enriched_result = db.client.table("llm_enrichment")\
    .select("id, job_postings!inner(title_classification)", count="exact")\
    .eq("job_postings.title_classification", "Data")\
    .not_.is_("enrichment_completed_at", "null")\
    .execute()
enriched = enriched_result.count or 0

print(f"Step 2 - Enriched Data jobs (completed enrichment): {enriched}")

# Calculate stats
unenriched = total - enriched
percentage = round((enriched / total * 100) if total > 0 else 0, 1)

print(f"\n=== RESULTS ===")
print(f"Total: {total}")
print(f"Enriched: {enriched}")
print(f"Unenriched: {unenriched}")
print(f"Percentage: {percentage}%")

print(f"\n=== EXPECTED UI DISPLAY ===")
print(f"AI Enriched: {enriched} / {total} ({percentage}%)")

# Verify: Check jobs that were Data but became NIS during enrichment
print(f"\n=== VERIFICATION ===")
print("Checking jobs that were 'Data' but classified as NIS during enrichment...")

# Get all Data jobs with completed enrichment
all_enriched_data = db.client.table("llm_enrichment")\
    .select("job_posting_id, type_datarol, job_postings!inner(title_classification)")\
    .eq("job_postings.title_classification", "Data")\
    .not_.is_("enrichment_completed_at", "null")\
    .limit(3000)\
    .execute()

# Count by type_datarol
nis_count = sum(1 for e in all_enriched_data.data if e.get("type_datarol") == "NIS")
other_count = sum(1 for e in all_enriched_data.data if e.get("type_datarol") == "Other")
data_roles_count = sum(1 for e in all_enriched_data.data if e.get("type_datarol") not in ["NIS", "Other", None])
null_count = sum(1 for e in all_enriched_data.data if e.get("type_datarol") is None)

print(f"  - Data roles (Data Engineer, etc.): {data_roles_count}")
print(f"  - NIS (classified during enrichment): {nis_count}")
print(f"  - Other: {other_count}")
print(f"  - NULL (incomplete enrichment): {null_count}")
print(f"  - Total enriched: {len(all_enriched_data.data)}")

print(f"\n✅ Jobs with title_classification='Data' but type_datarol='NIS' ARE counted as enriched: {nis_count} jobs")
