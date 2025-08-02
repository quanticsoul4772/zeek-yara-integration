# CI Configuration Update Required

## Issue #40: Python Version Standardization

Due to GitHub App workflow permissions, the following CI configuration changes need to be manually applied to `.github/workflows/ci.yml`:

### Changes Required:

1. **Update all Python version references from 3.9 to 3.12.5:**
   - Line 24: Change `python-version: '3.9'` to `python-version: '3.12.5'`
   - Line 133: Change `python-version: '3.9'` to `python-version: '3.12.5'`
   - Line 182: Change `python-version: '3.9'` to `python-version: '3.12.5'`
   - Line 221: Change `python-version: '3.9'` to `python-version: '3.12.5'`
   - Line 255: Change `python-version: '3.9'` to `python-version: '3.12.5'`
   - Line 316: Change `python-version: '3.9'` to `python-version: '3.12.5'`
   - Line 347: Change `python-version: '3.9'` to `python-version: '3.12.5'`

2. **Update the unit tests matrix from multiple Python versions to single version:**
   - Line 57: Change `python-version: ['3.8', '3.9', '3.10', '3.11']` to `python-version: ['3.12.5']`

3. **Update the codecov condition:**
   - Line 114: Change `matrix.python-version == '3.9'` to `matrix.python-version == '3.12.5'`

These changes will ensure all CI jobs use Python 3.12.5 consistently, eliminating the test environment inconsistencies described in the issue.

## Completed Changes:

✅ Added `.python-version` file with 3.12.5  
✅ Updated test runner (`bin/run_tests.sh`) with Python version check  
✅ Updated documentation (CLAUDE.md) with Python version requirement  
⏳ CI configuration update (manual intervention required)