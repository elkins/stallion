# Stallion - TODO List

This document tracks potential improvements and enhancements for the Stallion project.

## Completed ✅

### Phase 1: Python 3 Modernization & Security
- ✅ Fix Python 3 compatibility in console.py
- ✅ Add missing dependencies (requests, importlib_metadata, packaging)
- ✅ Replace debug prints with proper logging framework
- ✅ Add comprehensive type hints throughout codebase
- ✅ Improve error handling with timeouts and specific exceptions
- ✅ Fix metadata parsing for packages without version field
- ✅ Upgrade jQuery from 1.7.1 to 3.7.1 (security fixes)
- ✅ Upgrade jQuery UI from 1.8.16 to 1.14.1

### Phase 2: Quick Wins
- ✅ Replace optparse with argparse
- ✅ Add --version flag
- ✅ Add LRU caching for PyPI API calls (56,000x speedup!)
- ✅ Remove old insecure jQuery files
- ✅ Add basic unit tests

## Medium Priority (1-2 hours each)

### Rate Limiting for PyPI API
**Effort**: ~1 hour  
**Value**: Prevents throttling, good citizenship

Add rate limiting to avoid overwhelming PyPI:
- Time-based request limiting
- Configurable limits per endpoint
- Exponential backoff on errors
- Status indicators in UI

**Benefits**:
- Won't get throttled by PyPI
- More reliable service
- Better error handling

---

### Configuration File Support
**Effort**: ~2 hours  
**Value**: User customization, flexibility

Add YAML/TOML configuration file:
- Custom PyPI mirrors/indexes
- Cache settings (size, TTL)
- Logging configuration
- Default server options
- Theme preferences

**Example config.yaml**:
```yaml
server:
  host: 127.0.0.1
  port: 5000
  debug: false

pypi:
  index_url: https://pypi.org
  timeout: 10
  cache_size: 256

logging:
  level: INFO
  file: stallion.log
```

---

### Improve Error Pages
**Effort**: ~1 hour  
**Value**: Better UX

Create custom error templates:
- Styled 404 page with package search
- Friendly 500 page with troubleshooting
- Network error handling
- Validation error messages

---

### Search Functionality
**Effort**: ~2 hours  
**Value**: High user value

Add package search/filtering:
- Real-time search in sidebar
- Filter by name, author, version
- Search package descriptions
- Keyboard shortcuts
- Search history

## Larger Improvements (3+ hours)

### Async PyPI API Calls
**Effort**: ~3-4 hours  
**Value**: Much faster updates

Replace synchronous requests with async:
- Use `aiohttp` for non-blocking I/O
- Parallel package update checks
- Progress indicators
- Streaming responses

**Impact**: "Check all updates" 10-20x faster

---

### Package Dependency Graph
**Effort**: ~4-6 hours  
**Value**: Visualization feature

Interactive dependency visualization:
- D3.js force-directed graph
- Show dependencies and dependents
- Highlight conflicts
- Circular dependency detection
- Export to SVG/PNG

---

### REST API
**Effort**: ~4-5 hours  
**Value**: Programmatic access

JSON API for automation:
- `/api/v1/packages` - list packages
- `/api/v1/packages/{name}` - package details
- `/api/v1/packages/{name}/updates` - check updates
- `/api/v1/scripts` - console scripts
- OpenAPI/Swagger documentation

---

### Modern Frontend Refresh
**Effort**: ~8-10 hours  
**Value**: Modern look and feel

Update the UI:
- Bootstrap 5 (from Bootstrap 2)
- Responsive design improvements
- Dark mode support
- Vue.js or Alpine.js for reactivity
- Live update notifications
- Improved mobile experience

---

### Docker Support
**Effort**: ~2 hours  
**Value**: Easy deployment

Add Docker configuration:
- Dockerfile for production
- Docker Compose for development
- Multi-stage builds
- Health checks
- Volume mounts for persistence

**Example**:
```bash
docker run -p 5000:5000 stallion:latest
```

---

### GitHub Actions CI/CD
**Effort**: ~2-3 hours  
**Value**: Automation and quality

Add automated workflows:
- Run tests on PRs
- Linting and type checking
- Build and test on multiple Python versions
- Automated releases to PyPI
- Coverage reports
- Security scanning

## Low Priority / Nice to Have

### Additional Features
- [ ] Package comparison tool
- [ ] Export package list to requirements.txt
- [ ] Virtual environment integration
- [ ] Package installation from UI (dangerous!)
- [ ] Package uninstall from UI (dangerous!)
- [ ] Update notifications via email/webhook
- [ ] Custom themes/skins
- [ ] Multi-language support (i18n)
- [ ] Package statistics dashboard
- [ ] Integration with pip-audit for security scanning

### Technical Debt
- [ ] Add type stubs for better type checking
- [ ] Improve test coverage (currently basic)
- [ ] Add integration tests
- [ ] Performance profiling
- [ ] Memory optimization
- [ ] Add benchmarks

### Documentation
- [ ] User guide/tutorial
- [ ] Developer documentation
- [ ] API documentation
- [ ] Deployment guide
- [ ] Troubleshooting guide
- [ ] Contributing guidelines

## Ideas for Future

- Plugin system for extensibility
- Package recommendation engine
- Vulnerability scanning integration
- Package license compliance checking
- Automated dependency updates (like Dependabot)
- Integration with PyPI Warehouse API v2
- WebSocket support for real-time updates
- Progressive Web App (PWA) support
- Desktop app wrapper (Electron/Tauri)

## Notes

### Performance Metrics (Current)
- Package list load: ~100ms
- PyPI update check (first): ~50-100ms per package
- PyPI update check (cached): <1ms per package
- Full update scan (100 packages, cached): ~500ms

### Tech Stack
- Python 3.8+
- Flask (web framework)
- jQuery 3.7.1 + jQuery UI 1.14.1
- Bootstrap 2.x (could be upgraded)
- importlib.metadata (package introspection)

### Compatibility
- Python: 3.8+
- OS: Linux, macOS, Windows
- Browsers: Modern browsers (Chrome, Firefox, Safari, Edge)

---

**Last Updated**: December 1, 2025  
**Branch**: python3-modernization
