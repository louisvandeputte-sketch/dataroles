#!/usr/bin/env python3
"""Merge duplicate company entries (auto-confirm)."""

from database.client import db
from collections import defaultdict

print("Company Deduplication (Auto-confirm)")
print("=" * 80)

# Get all companies
companies = db.client.table("companies")\
    .select("id, name, linkedin_company_id")\
    .execute()

# Group by name
by_name = defaultdict(list)
for company in companies.data:
    by_name[company['name']].append(company)

# Find duplicates
duplicates = {name: comps for name, comps in by_name.items() if len(comps) > 1}

print(f"\n📊 Found {len(duplicates)} company names with duplicates")
print(f"📋 Total duplicate entries: {sum(len(comps) for comps in duplicates.values())}")

# Strategy
print(f"\n🔧 Merge Strategy:")
print(f"  1. Keep company with logo (highest priority)")
print(f"  2. Keep company with linkedin_company_id")
print(f"  3. Keep company with most jobs")
print(f"  4. Merge all jobs to the kept company")
print(f"  5. Delete duplicate companies")
print(f"\n🚀 Starting merge...")

merged_count = 0
deleted_count = 0
jobs_moved = 0

for name, companies_list in duplicates.items():
    print(f"\n📦 Processing: {name} ({len(companies_list)} entries)")
    
    # Get full company data including logo
    full_companies = []
    for company in companies_list:
        full = db.client.table("companies")\
            .select("id, name, linkedin_company_id, logo_data, logo_url")\
            .eq("id", company['id'])\
            .single()\
            .execute()
        
        # Count jobs
        job_count = db.client.table("job_postings")\
            .select("id", count="exact")\
            .eq("company_id", company['id'])\
            .execute()
        
        full_companies.append({
            **full.data,
            'job_count': job_count.count
        })
    
    # Determine which to keep - Priority:
    # 1. Has logo_data (profile photo)
    # 2. Has linkedin_company_id
    # 3. Most jobs
    def score_company(c):
        score = 0
        if c.get('logo_data'):
            score += 1000  # Highest priority
        if c.get('logo_url'):
            score += 500
        if c.get('linkedin_company_id'):
            score += 100
        score += c.get('job_count', 0)  # Job count as tiebreaker
        return score
    
    # Sort by score
    full_companies.sort(key=score_company, reverse=True)
    keep = full_companies[0]
    to_delete = [c for c in full_companies if c['id'] != keep['id']]
    
    reasons = []
    if keep.get('logo_data'):
        reasons.append("✨ has logo")
    if keep.get('linkedin_company_id'):
        reasons.append(f"🔗 LinkedIn ID: {keep['linkedin_company_id']}")
    if keep.get('job_count', 0) > 0:
        reasons.append(f"💼 {keep['job_count']} jobs")
    
    reason_str = ", ".join(reasons) if reasons else "first entry"
    print(f"  ✅ Keeping: {keep['id'][:20]}... ({reason_str})")
    
    # Merge jobs from duplicates to kept company
    for dup in to_delete:
        # Get jobs for this duplicate
        jobs = db.client.table("job_postings")\
            .select("id")\
            .eq("company_id", dup['id'])\
            .execute()
        
        if jobs.data:
            print(f"  🔀 Merging {len(jobs.data)} jobs from {dup['id'][:20]}...")
            
            # Update all jobs to point to kept company
            for job in jobs.data:
                db.client.table("job_postings")\
                    .update({"company_id": keep['id']})\
                    .eq("id", job['id'])\
                    .execute()
            
            jobs_moved += len(jobs.data)
        
        # Delete duplicate company
        print(f"  🗑️  Deleting duplicate: {dup['id'][:20]}...")
        db.client.table("companies")\
            .delete()\
            .eq("id", dup['id'])\
            .execute()
        
        deleted_count += 1
    
    merged_count += 1

print(f"\n" + "=" * 80)
print(f"✅ Merge complete!")
print(f"  📦 Merged: {merged_count} company names")
print(f"  🗑️  Deleted: {deleted_count} duplicate entries")
print(f"  💼 Jobs moved: {jobs_moved}")
print(f"  🏢 Remaining companies: {len(companies.data) - deleted_count}")
