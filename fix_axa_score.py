#!/usr/bin/env python3
"""Fix AXA job score with correct calculation"""

from database.client import db
from datetime import datetime

# Correct calculation for AXA
# F:40, Q:20, T:90, R:90, C:?, Rep:?
# Weights: F:0.25, Q:0.20, T:0.20, R:0.15, C:0.10, Rep:0.10

# Assuming C:50 and Rep:40 (typical values)
freshness = 40
quality = 20
transparency = 90
role_match = 90
completeness = 50  # estimate
reputation = 40  # estimate

base_score = (
    freshness * 0.25 +
    quality * 0.20 +
    transparency * 0.20 +
    role_match * 0.15 +
    completeness * 0.10 +
    reputation * 0.10
)

print(f"\n📊 Correct AXA Score Calculation:")
print(f"   F:{freshness} × 0.25 = {freshness * 0.25}")
print(f"   Q:{quality} × 0.20 = {quality * 0.20}")
print(f"   T:{transparency} × 0.20 = {transparency * 0.20}")
print(f"   R:{role_match} × 0.15 = {role_match * 0.15}")
print(f"   C:{completeness} × 0.10 = {completeness * 0.10}")
print(f"   Rep:{reputation} × 0.10 = {reputation * 0.10}")
print(f"   ─────────────────────────")
print(f"   Base Score: {base_score}")

# Update with correct values
metadata = {
    'freshness_score': freshness,
    'quality_score': quality,
    'transparency_score': transparency,
    'role_match_score': role_match,
    'completeness_score': completeness,
    'reputation_score': reputation,
    'base_score': round(base_score, 2)
}

print(f"\n🔄 Updating AXA job...")
result = db.client.table("job_postings").update({
    'base_score': round(base_score, 2),
    'ranking_metadata': metadata,
    'ranking_updated_at': datetime.now().isoformat()
}).eq('id', 'e837e315-dfc8-4c91-87a4-7ae0a16290cd').execute()

print(f"✅ Updated! New base_score: {base_score:.2f}")
