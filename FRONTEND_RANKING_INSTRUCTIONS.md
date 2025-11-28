# Frontend Ranking Instructions

## ❌ CURRENT IMPLEMENTATION (WRONG)

Your frontend is currently using:
- **Table:** `llm_enrichment_active` 
- **Column:** `ranking_position`
- **Sort:** ASC (lower = better)

**This is INCORRECT!** The `ranking_position` is outdated and not maintained.

---

## ✅ CORRECT IMPLEMENTATION

Use the **`vw_job_listings`** view with the following columns:

### **Primary Sort Column:**
```sql
ranking_score DESC  -- Higher score = better job
```

### **Available Ranking Columns in `vw_job_listings`:**

| Column | Type | Description | Usage |
|--------|------|-------------|-------|
| `ranking_score` | FLOAT | **Final score** (updated hourly) | **PRIMARY SORT** - Use this! |
| `base_score` | FLOAT | Stable base score (updated nightly) | Secondary sort if needed |
| `ranking_position` | INT | Position in ranking (1 = best) | Alternative (but use score!) |
| `hourly_multiplier` | FLOAT | Random multiplier (0.8-1.2) | For display/debugging |
| `ranking_metadata` | JSONB | Score breakdown (F/Q/T/R) | For detailed display |

### **Recommended Sort Order:**

```sql
ORDER BY 
  ranking_score DESC,           -- Primary: Highest score first
  posted_date_corrected DESC    -- Fallback: Newest jobs first
```

### **Alternative (using position):**

```sql
ORDER BY 
  ranking_position ASC,         -- Primary: Position 1 = best
  posted_date_corrected DESC    -- Fallback: Newest jobs first
```

---

## 📊 Score Breakdown Display

The `ranking_metadata` JSONB contains:

```json
{
  "freshness_score": 40,      // F: Job age (0-150, MEGA BOOST ≤30h)
  "quality_score": 20,         // Q: AI enrichment quality (0-100)
  "transparency_score": 90,    // T: Direct hiring, apply URL (0-100)
  "role_match_score": 90,      // R: Data role match (0-100)
  "completeness_score": 50,    // C: Data completeness (0-100)
  "reputation_score": 40,      // Rep: Company reputation (0-100)
  "base_score": 54.5          // Weighted sum of above
}
```

You can display this as: `F:40 Q:20 T:90 R:90`

---

## 🔄 Update Frequency

- **`ranking_score`**: Updated **every hour** (base_score × hourly_multiplier)
- **`base_score`**: Updated **nightly** (full recalculation)
- **`hourly_multiplier`**: Changes **every hour** (0.8-1.2 random)
- **`ranking_position`**: Updated **every hour** (derived from ranking_score)

---

## 📅 Date Fields

| Column | Description | Use Case |
|--------|-------------|----------|
| `posted_date` | Date from job platform | Display "Posted on" |
| `first_seen_at` | First scrape date | Show when we found it |
| `posted_date_corrected` | MIN(first_seen, posted) | **Use for age calculation** |

**Always use `posted_date_corrected` for freshness calculations!**

---

## 🎯 Example Query

```sql
SELECT 
  job_posting_id,
  title,
  company_name,
  ranking_score,
  ranking_position,
  ranking_metadata,
  posted_date,
  posted_date_corrected,
  first_seen_at
FROM vw_job_listings
WHERE title_classification = 'Data'
  AND is_active = TRUE
ORDER BY 
  ranking_score DESC,
  posted_date_corrected DESC
LIMIT 50;
```

---

## 🚨 Important Notes

1. **Never use `llm_enrichment_active.ranking_position`** - it's not maintained
2. **Always use `vw_job_listings`** - it has all ranking data
3. **Sort by `ranking_score DESC`** - higher is better
4. **Use `posted_date_corrected`** - more accurate than `posted_date`
5. **Jobs without scores** get `ranking_score = NULL` and should appear last

---

## 💡 Display Recommendations

### Job Card:
```
Score: 86.7  (color-coded: green >80, blue 50-80, gray <50)
Calculation: F:150 Q:27 T:70 R:100
Posted: 27-11-2025 (📅 02-11-2025 if corrected differs)
```

### Color Coding:
- 🟢 **> 80**: Excellent job (green)
- 🔵 **50-80**: Good job (blue)
- ⚫ **0-50**: Average job (gray)
- 🔴 **< 0**: Non-enriched job (red) - should be hidden

---

## 📞 Questions?

Contact the backend team if you need:
- Additional columns in `vw_job_listings`
- Different sort options
- Custom filtering logic
