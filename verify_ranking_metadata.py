#!/usr/bin/env python3
"""Verify that ranking_metadata matches actual scores"""

from database.client import db

# Get a few jobs to verify
result = db.client.table("job_postings")\
    .select("id, title, company_id, base_score, ranking_score, hourly_multiplier, ranking_metadata")\
    .not_.is_("ranking_metadata", "null")\
    .limit(10)\
    .execute()

print("\n🔍 Verifying ranking metadata consistency:\n")

for job in result.data:
    meta = job['ranking_metadata']
    
    # Calculate expected final score
    expected_final = job['base_score'] * job['hourly_multiplier'] if job['base_score'] and job['hourly_multiplier'] else None
    
    # Get metadata values
    meta_base = meta.get('base_score')
    actual_final = job['ranking_score']
    
    # Check if they match
    base_match = abs(meta_base - job['base_score']) < 0.1 if meta_base and job['base_score'] else False
    final_match = abs(expected_final - actual_final) < 0.1 if expected_final and actual_final else False
    
    status = "✅" if base_match and final_match else "❌"
    
    print(f"{status} {job['title'][:50]}")
    print(f"   Base:  DB={job['base_score']:.1f}  Meta={meta_base:.1f}  Match={base_match}")
    print(f"   Mult:  {job['hourly_multiplier']:.3f}")
    print(f"   Final: DB={actual_final:.1f}  Calc={expected_final:.1f}  Match={final_match}")
    print()
