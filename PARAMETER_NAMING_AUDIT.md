# 🔍 Parameter Naming Audit - Complete Analysis

## Executive Summary

✅ **All function calls are now CORRECT**
⚠️ **One mismatch was found and FIXED**: `web/api/queries.py`

## Function Signatures

### 1. `execute_scrape_run()` - scraper/orchestrator.py

**Signature:**
```python
async def execute_scrape_run(
    query: str,           # ← NOT 'search_query'
    location: str,        # ← NOT 'location_query'
    lookback_days: Optional[int] = None
) -> ScrapeRunResult:
```

**All Call Sites:**
| File | Line | Status | Parameters |
|------|------|--------|------------|
| `web/api/queries.py` | 128 | ✅ FIXED | `query=`, `location=`, `lookback_days=` |
| `test_orchestrator.py` | 19 | ✅ CORRECT | `query=`, `location=` |
| `test_orchestrator.py` | 57 | ✅ CORRECT | `query=`, `location=`, `lookback_days=` |
| `test_orchestrator.py` | 82 | ✅ CORRECT | Positional args (correct order) |

### 2. `determine_date_range()` - scraper/date_strategy.py

**Signature:**
```python
def determine_date_range(
    query: str,
    location: str,
    lookback_days: Optional[int] = None
) -> Tuple[str, int]:
```

**All Call Sites:**
| File | Line | Status | Parameters |
|------|------|--------|------------|
| `scraper/orchestrator.py` | 86 | ✅ CORRECT | `query`, `location`, `lookback_days` |
| `tests/test_date_strategy.py` | 52 | ✅ CORRECT | Positional + keyword args |
| `tests/test_date_strategy.py` | 65+ | ✅ CORRECT | Positional args |

### 3. `should_trigger_scrape()` - scraper/date_strategy.py

**Signature:**
```python
def should_trigger_scrape(
    query: str,
    location: str,
    min_interval_hours: int = 6
) -> bool:
```

**All Call Sites:**
| File | Line | Status | Parameters |
|------|------|--------|------------|
| `tests/test_date_strategy.py` | 153+ | ✅ CORRECT | Positional + keyword args |

### 4. `mark_inactive_jobs()` - scraper/lifecycle.py

**Signature:**
```python
def mark_inactive_jobs(
    threshold_days: int = 14
) -> int:
```

**All Call Sites:**
| File | Line | Status | Parameters |
|------|------|--------|------------|
| `web/api/quality.py` | 63 | ✅ CORRECT | `threshold_days=` |
| `tests/test_lifecycle.py` | 39+ | ✅ CORRECT | `threshold_days=` |

### 5. `get_inactive_jobs_summary()` - scraper/lifecycle.py

**Signature:**
```python
def get_inactive_jobs_summary() -> dict:
```

**All Call Sites:**
| File | Line | Status | Parameters |
|------|------|--------|------------|
| `web/api/quality.py` | 43 | ✅ CORRECT | No parameters |
| `tests/test_lifecycle.py` | 145+ | ✅ CORRECT | No parameters |

## Database vs API Naming Convention

### Database Schema (scrape_runs table)
```sql
CREATE TABLE scrape_runs (
    search_query TEXT NOT NULL,    -- Database uses 'search_query'
    location_query TEXT NOT NULL,  -- Database uses 'location_query'
    ...
);
```

### Python Function Parameters
```python
# Functions use shorter names:
def execute_scrape_run(
    query: str,      # NOT 'search_query'
    location: str,   # NOT 'location_query'
    ...
):
```

### API Request/Response Models
```python
# API models match database naming:
class QueryCreate(BaseModel):
    search_query: str      # Matches database
    location_query: str    # Matches database
    lookback_days: int
```

## Why The Mismatch Existed

### The Problem
```python
# WRONG (before fix):
background_tasks.add_task(
    execute_scrape_run,
    search_query=query.search_query,  # ❌ Wrong parameter name
    location_query=query.location_query,  # ❌ Wrong parameter name
    lookback_days=query.lookback_days
)
```

### The Fix
```python
# CORRECT (after fix):
background_tasks.add_task(
    execute_scrape_run,
    query=query.search_query,  # ✅ Correct parameter name
    location=query.location_query,  # ✅ Correct parameter name
    lookback_days=query.lookback_days
)
```

## Naming Convention Summary

| Context | Query Parameter | Location Parameter |
|---------|----------------|-------------------|
| **Database columns** | `search_query` | `location_query` |
| **API models** | `search_query` | `location_query` |
| **Function parameters** | `query` | `location` |
| **Display/UI** | "Query" or "Search Query" | "Location" |

## Why Different Names?

1. **Database**: Uses descriptive names (`search_query`, `location_query`) for clarity in SQL
2. **API Models**: Matches database for consistency
3. **Functions**: Uses shorter names (`query`, `location`) for cleaner code
4. **Mapping**: API models map to function parameters at call site

## Verification Checklist

- [x] `execute_scrape_run()` - All calls use `query=`, `location=`
- [x] `determine_date_range()` - All calls use `query`, `location`
- [x] `should_trigger_scrape()` - All calls use `query`, `location`
- [x] `mark_inactive_jobs()` - All calls use `threshold_days=`
- [x] `get_inactive_jobs_summary()` - All calls correct (no params)
- [x] No other mismatches found

## Testing

### Manual Test
```bash
# This should work now:
curl -X POST http://localhost:8000/api/queries/run-now \
  -H "Content-Type: application/json" \
  -d '{
    "search_query": "Test Query",
    "location_query": "Test Location",
    "lookback_days": 7
  }'

# Expected: Scrape starts successfully
```

### Automated Tests
```bash
# All tests should pass:
./venv/bin/pytest tests/test_date_strategy.py -v
./venv/bin/pytest tests/test_lifecycle.py -v
./venv/bin/pytest tests/test_orchestrator.py -v
```

## Recommendations

### 1. Add Type Hints Everywhere
```python
# Good:
def execute_scrape_run(
    query: str,
    location: str,
    lookback_days: Optional[int] = None
) -> ScrapeRunResult:
    ...
```

### 2. Use Explicit Keyword Arguments
```python
# Prefer this:
execute_scrape_run(
    query="Data Engineer",
    location="Netherlands",
    lookback_days=7
)

# Over this:
execute_scrape_run("Data Engineer", "Netherlands", 7)
```

### 3. Document Parameter Mapping
```python
# In API endpoint:
background_tasks.add_task(
    execute_scrape_run,
    query=query.search_query,  # API model -> function param
    location=query.location_query,  # API model -> function param
    lookback_days=query.lookback_days
)
```

### 4. Add Validation
```python
# In Pydantic models:
class QueryCreate(BaseModel):
    search_query: str = Field(..., min_length=1, max_length=200)
    location_query: str = Field(..., min_length=1, max_length=200)
    lookback_days: int = Field(default=7, ge=1, le=30)
```

## Future Improvements

### Option 1: Standardize on One Naming Convention
```python
# Everywhere use 'query' and 'location':
CREATE TABLE scrape_runs (
    query TEXT NOT NULL,      # Shorter
    location TEXT NOT NULL,   # Shorter
    ...
);
```

### Option 2: Use Dataclass for Parameters
```python
@dataclass
class ScrapeQuery:
    query: str
    location: str
    lookback_days: int = 7

# Then:
def execute_scrape_run(params: ScrapeQuery) -> ScrapeRunResult:
    ...
```

### Option 3: Add Parameter Validation Decorator
```python
def validate_params(func):
    def wrapper(*args, **kwargs):
        # Check parameter names match function signature
        ...
    return wrapper

@validate_params
async def execute_scrape_run(query: str, location: str, ...):
    ...
```

## Conclusion

✅ **All parameter naming issues have been identified and fixed**
✅ **Only one mismatch existed: `web/api/queries.py` (now fixed)**
✅ **All other code uses correct parameter names**
✅ **Tests verify correct usage**

**Status**: AUDIT COMPLETE - NO REMAINING ISSUES

---

**Last Updated**: 2025-10-09 22:44
**Audited Files**: 15+ Python files
**Issues Found**: 1 (fixed)
**Issues Remaining**: 0
