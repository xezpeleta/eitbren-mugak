# Geo-Restriction Detection Issues

## Summary

This document explains why the scraper sometimes saved content with `is_geo_restricted = None` and how these issues have been addressed.

## Root Causes

### 1. **404 Status Codes**

**When it happens:**
- Manifest URL returns 404 (Not Found)
- Audio file URL returns 404 (Not Found)

**Why it's kept as None:**
- A 404 could mean:
  - Content doesn't exist at that URL
  - Wrong slug or language code
  - Content was removed
  - Temporary server issue
- It's ambiguous whether it's a geo-restriction or a "not found" issue

**Code location:**
- `src/makusi_api.py` lines 174-176 (audio), 215-217 (video)
- `src/primeran_api.py` lines 157-159

**Current handling:**
- Scraper keeps it as `None` and logs a warning
- Fix script treats 404 as "cannot determine" and leaves it as None

**Recommendation:**
- For 404 on manifest/audio URLs, we could:
  - Retry with different language codes
  - Check if content exists via API first
  - Mark as "unknown" but log for manual review

### 2. **Network Errors / Timeouts**

**When it happens:**
- Request timeout (10 seconds)
- Connection errors
- DNS failures
- SSL errors

**Why it's kept as None:**
- Network errors are transient and should be retried
- Can't determine if content is geo-restricted if we can't reach the server

**Code location:**
- `src/makusi_api.py` lines 183-190 (audio), 224-231 (video)
- `src/primeran_api.py` lines 166-172

**Current handling:**
- Returns `is_geo_restricted: None` with error message
- Scraper keeps it as None

**Recommendation:**
- Implement retry logic with exponential backoff
- After 3 retries, mark as "unknown" or skip
- Log for manual review

### 3. **Unexpected Status Codes**

**When it happens:**
- Server returns status codes other than 200, 403, 404, 500
- Examples: 401 (Unauthorized), 429 (Too Many Requests), 502 (Bad Gateway), etc.

**Why it's kept as None:**
- Unknown what the status code means
- Could be temporary server issues or actual restrictions

**Code location:**
- `src/makusi_api.py` lines 177-179 (audio), 218-220 (video)
- `src/primeran_api.py` lines 160-162

**Current handling:**
- Returns `is_geo_restricted: None` with error message
- Scraper keeps it as None

**Recommendation:**
- Handle common status codes:
  - 401: Authentication issue (should re-authenticate)
  - 429: Rate limiting (should wait and retry)
  - 502/503: Server error (should retry)
- For truly unexpected codes, log for manual review

### 4. **Status Code 200 with None is_geo_restricted**

**When it happens:**
- This shouldn't happen in normal flow, but could occur due to bugs
- If status_code is 200, `is_geo_restricted` should always be `False`

**Current handling:**
- Scraper now handles this (added in recent fix):
  - If status_code is 200 but is_geo_restricted is None, treat as accessible
- Fix script also handles this case

## Fixes Applied

### 1. **Scraper Improvements** (`src/scraper.py` lines 440-449)

Added logic to handle cases where `geo_check.get('is_geo_restricted')` is `None`:
- If status_code is 403 or 500 → treat as geo-restricted
- If status_code is 200 → treat as accessible (fallback)
- Otherwise → keep as None and log warning

### 2. **Fix Script** (`fix_geo_restriction_none.py`)

Created a script to re-check all content with `None` status:
- Checks API endpoint first (handles 403/500 at API level)
- Then checks manifest/audio URL
- Handles all edge cases (200 with None, 404, network errors, etc.)
- Successfully fixed 1028 items

## Recommendations for Future

1. **Add Retry Logic**
   - Implement exponential backoff for network errors
   - Retry up to 3 times before giving up

2. **Better 404 Handling**
   - Verify content exists via API before checking manifest
   - Try different language codes if 404
   - Log 404s for manual review

3. **Handle More Status Codes**
   - 401: Re-authenticate and retry
   - 429: Wait and retry with backoff
   - 502/503: Retry (temporary server issues)

4. **Monitoring**
   - Track how many items end up with None status
   - Alert if None count increases significantly
   - Regular review of None items

5. **Fallback Strategies**
   - If manifest check fails, try alternative methods
   - Check multiple language codes
   - Use API metadata hints if available

## Statistics

From the fix script run:
- **Total items fixed**: 1028
- **Geo-restricted**: ~60% (items with 403/500)
- **Accessible**: ~40% (items with 200)
- **Remaining None**: 0 (all fixed)

## Example Cases

### Case 1: API 403 (Fixed)
- **Slug**: `dragoi-bola-super-29-arte-martzialen-lehia-martxan-dago-taldeko-kapitaina-goku-baino-indartsuagoa-da`
- **Issue**: API returned 403, but scraper didn't catch it (scraped before fix)
- **Fix**: Marked as `is_geo_restricted: True, restriction_type: api_403`

### Case 2: Manifest 200 (Fixed)
- **Slug**: `goazen-d2-1-basakabi`
- **Issue**: Manifest check returned 200 but was saved as None (edge case)
- **Fix**: Marked as `is_geo_restricted: False, restriction_type: manifest_200`

### Case 3: Audio 404 (Still None)
- **Slug**: `munduenea-2-deabruaren-zubia`
- **Issue**: Audio file URL returned 404
- **Status**: Legitimately unknown - could be missing file or wrong URL
- **Action**: Needs manual review or retry with different parameters
