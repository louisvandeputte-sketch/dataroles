#!/usr/bin/env python3
"""Test relevance scorer with various tech items."""

from ingestion.relevance_scorer import score_relevance

# Test cases
test_items = [
    "Python",
    "SQL",
    "R",
    "JavaScript",
    "Spark",
    "Snowflake",
    "Power BI",
    "Tableau",
    "Excel",
    "Oracle Data Integrator",
    "XSLT",
    "Fortran",
    "dbt",
    "Airflow",
    "Kubernetes",
    "Docker"
]

print("🧪 Testing Relevance Scorer")
print("=" * 60)

results = []

for item in test_items:
    score, error = score_relevance(item)
    
    if score is not None:
        results.append((item, score))
        print(f"✅ {item:30} → {score:3}/100")
    else:
        print(f"❌ {item:30} → ERROR: {error}")

print("\n" + "=" * 60)
print("📊 Results Summary")
print("=" * 60)

# Sort by score
results.sort(key=lambda x: x[1], reverse=True)

print("\nTop 5 Most Relevant:")
for item, score in results[:5]:
    print(f"  {score:3}/100 - {item}")

print("\nBottom 5 Least Relevant:")
for item, score in results[-5:]:
    print(f"  {score:3}/100 - {item}")

print(f"\n✅ Tested {len(results)}/{len(test_items)} items successfully")
