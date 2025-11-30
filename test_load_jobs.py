#!/usr/bin/env python3
"""Test if all jobs are loaded by the ranking system"""

from ranking.job_ranker import load_jobs_from_database

print("\n🔍 Testing job loading...\n")

# Load jobs
jobs = load_jobs_from_database()

print(f"\n📊 Loaded {len(jobs)} jobs")

# Count by classification
data_jobs = [j for j in jobs if j.title_classification == "Data"]
nis_jobs = [j for j in jobs if j.title_classification == "NIS"]
other_jobs = [j for j in jobs if j.title_classification == "Other"]

print(f"   Data: {len(data_jobs)}")
print(f"   NIS: {len(nis_jobs)}")
print(f"   Other: {len(other_jobs)}")

# Check if our 8 problem jobs are in the loaded set
problem_job_ids = [
    "7ec45673-ce07-4898-b1c8-fbc3383684f6",  # Senior Product Owner
    "bc38bc96-a4d7-4b0e-90c3-4fd065ff0009",  # Data-analist
    "aa8264e8-b6ca-4fa1-a25a-f2b1e00030cc",  # Technical Solution Architect
    "8adfd83a-63b6-42b3-bba5-d85b999d0e66",  # Senior Engineer
    "dc55c32f-923d-4fc0-bc96-af834a409433",  # Analist Managementrapporteringen
    "e2d8605d-8d54-4f37-b358-915a213cc959",  # Researcher
    "86646b53-62e8-43f1-a005-eda9ba9b7881",  # HR Data & Insights Manager
    "b4f5f295-4199-4b1b-97c6-f881ebcab340",  # Financial Planning & Analysis
]

loaded_ids = {j.id for j in jobs}

print(f"\n🔍 Checking if problem jobs are loaded:")
for job_id in problem_job_ids:
    if job_id in loaded_ids:
        job = next(j for j in jobs if j.id == job_id)
        print(f"   ✅ {job.title[:50]}")
        print(f"      Classification: {job.title_classification}")
        print(f"      Is active: {job.is_active}")
    else:
        print(f"   ❌ Job {job_id[:8]}... NOT loaded")
