# Security Notes

## JavaScript Dependencies

### jQuery Version - ✅ FIXED
**Status**: Updated from jQuery 1.7.1 to jQuery 3.7.1 (latest stable)

The project previously used jQuery 1.7.1 (released 2011), which had known security vulnerabilities including:
- XSS vulnerabilities (CVE-2015-9251, CVE-2019-11358, CVE-2020-11022, CVE-2020-11023)
- Prototype pollution issues

**Current Version**: jQuery 3.7.1 (Dec 2024) - All known vulnerabilities patched
**jQuery UI Version**: 1.14.1 (latest stable)

### Files Updated:
- `stallion/static/jquery-3.7.1.min.js` (87 KB)
- `stallion/static/jquery-ui-1.14.1.min.js` (253 KB)
- `stallion/static/jquery-ui-1.14.1.min.css` (30 KB)
- `stallion/templates/main.html` (references updated)

## Network Security

### PyPI API Calls
- All PyPI API calls now use HTTPS
- Timeouts are set to 10 seconds to prevent hanging
- Proper error handling for network failures

### Rate Limiting
Consider implementing rate limiting for PyPI API calls to avoid:
- Being throttled by PyPI
- Excessive bandwidth usage
- Slow page loads

### Recommendations
1. Implement caching for PyPI API responses (e.g., Redis, in-memory cache)
2. Add rate limiting per package/per hour
3. Consider using conditional requests (ETag/If-Modified-Since)
