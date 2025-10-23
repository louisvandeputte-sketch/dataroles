# Test Scripts

This directory contains test scripts for debugging and validation.

## Available Tests

### `test_scrape_flow.py`
Complete end-to-end test of the scrape workflow:
- Database connection
- Bright Data API connection
- Scrape run creation/update
- Error handling validation

**Usage:**
```bash
python tests/test_scrape_flow.py
```

### `test_brightdata_direct.py`
Direct test of Bright Data API with aggressive timeouts:
- Tests API connectivity
- Validates trigger endpoint
- Helps diagnose timeout issues

**Usage:**
```bash
python tests/test_brightdata_direct.py
```

## Running Tests

All tests can be run from the project root directory:

```bash
# Run all tests
python -m pytest tests/

# Run specific test
python tests/test_scrape_flow.py
```

## Notes

- Tests use the real Bright Data API (not mock)
- Some tests create actual scrape runs in the database
- Test runs are marked with `"test": True` in metadata
