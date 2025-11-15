# Archived Templates

This folder contains old/deprecated template files that are no longer in use.

## Archived Files

### `runs_linkedin_old.html` (formerly `runs.html`)
- **Status**: DEPRECATED
- **Replaced by**: `scraper_runs.html`
- **Reason**: Separate LinkedIn-only runs page replaced by unified LinkedIn+Indeed page
- **Routes**: `/runs` now redirects to `/scraper-runs`

### `runs_indeed_old.html` (formerly `indeed_runs.html`)
- **Status**: DEPRECATED
- **Replaced by**: `scraper_runs.html`
- **Reason**: Separate Indeed-only runs page replaced by unified LinkedIn+Indeed page
- **Routes**: `/indeed/runs` now redirects to `/scraper-runs`

## Current Active Template

**`scraper_runs.html`** - Unified scraper runs page showing both LinkedIn and Indeed runs
- Route: `/scraper-runs`
- Features:
  - Combined view of LinkedIn and Indeed runs
  - Source filter (All/LinkedIn/Indeed)
  - View Jobs button for each run
  - Details modal
  - Archive functionality

## Why Archived?

These templates were causing confusion with multiple runs pages. The unified `scraper_runs.html` provides:
- Single source of truth for all scrape runs
- Better UX with source filtering
- Consistent interface for both platforms
- Easier maintenance

## Migration Notes

All routes have been updated with 301 redirects:
- `/runs` → `/scraper-runs`
- `/indeed/runs` → `/scraper-runs`

No code changes needed - redirects handle backward compatibility.
