#!/usr/bin/env python3
"""Manually fix GeoDynamics job score"""

from database.client import db
from datetime import datetime

geodyn_id = "faf12622-68b4-477e-9ca2-59527485cdb1"

# Correct scores for 26 days old job
# F:40, Q:27, T:70, R:100
freshness = 40  # 26 days = F:40
quality = 27
transparency = 70
role_match = 100
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

print(f"\n📊 Correct GeoDynamics Score:")
print(f"   F:{freshness} Q:{quality} T:{transparency} R:{role_match}")
print(f"   Base Score: {base_score:.1f}")

metadata = {
    'freshness_score': freshness,
    'quality_score': quality,
    'transparency_score': transparency,
    'role_match_score': role_match,
    'completeness_score': completeness,
    'reputation_score': reputation,
    'base_score': round(base_score, 2)
}

print(f"\n🔄 Updating GeoDynamics job...")
result = db.client.table("job_postings").update({
    'base_score': round(base_score, 2),
    'ranking_metadata': metadata,
    'ranking_updated_at': datetime.now().isoformat()
}).eq('id', geodyn_id).execute()

print(f"✅ Updated! New base_score: {base_score:.2f}")
print(f"   Old: Base:80.9 F:150")
print(f"   New: Base:{base_score:.1f} F:40")
