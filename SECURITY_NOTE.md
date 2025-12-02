# Security Notes

## JavaScript Dependencies

### jQuery Version
The project currently uses jQuery 1.7.1 (released 2011), which has known security vulnerabilities including:
- XSS vulnerabilities (CVE-2015-9251, CVE-2019-11358, CVE-2020-11022, CVE-2020-11023)
- Prototype pollution issues

**Recommendation**: Update to jQuery 3.7.x or later, which includes security fixes.

### Upgrade Path
To upgrade jQuery:

1. Replace `stallion/static/jquery-1.7.1.min.js` with a modern version
2. Replace `stallion/static/jquery-ui-1.8.16.custom.min.js` with a compatible version
3. Update template references in `stallion/templates/*.html`
4. Test all interactive features:
   - Package search/filtering
   - AJAX updates for PyPI version checks
   - UI interactions

### CDN Alternative
Consider using a CDN for jQuery to automatically get security updates:
```html
<script src="https://code.jquery.com/jquery-3.7.1.min.js" 
        integrity="sha256-/JqT3SQfawRcv/BIHPThkBvs0OEvtFFmqPF/lYI/Cxo=" 
        crossorigin="anonymous"></script>
```

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
