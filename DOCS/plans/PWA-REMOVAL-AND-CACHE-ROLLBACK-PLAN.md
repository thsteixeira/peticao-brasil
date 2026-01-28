# PWA Removal and Cache Versioning Rollback Plan

**Date:** January 27, 2026  
**Purpose:** Comprehensive plan to remove all PWA (Progressive Web App) functionality and reverse all changes made attempting to fix CSS caching issues

---

## Executive Summary

This document provides a step-by-step plan to:
1. **Remove all PWA functionality** from the Petição Brasil platform
2. **Reverse cache versioning changes** that were implemented to fix CSS caching issues
3. **Restore the project** to a simpler, non-PWA state
4. **Clean up related files, code, and documentation**

### Why Remove PWA?

The PWA implementation introduced significant complexity and caused persistent caching issues:
- CSS files not loading properly after updates
- Service worker aggressively caching static assets
- Complex cache invalidation strategies causing inconsistent behavior
- Multiple failed attempts to fix caching with increasing complexity
- Better suited for a production-ready app, not a prototype/TCC project

---

## Current State Analysis

### PWA-Related Files

#### 1. Service Worker & Registration
- **`templates/service-worker.js`** (273 lines) - Core service worker with caching strategies
- **`static/js/pwa-register.js`** (258 lines) - Service worker registration and installation UI
- Note: `static/js/service-worker.js` was moved to `templates/` directory

#### 2. PWA Views & URLs
- **`apps/core/pwa_views.py`** (143 lines) - Views for manifest, service worker, offline page, PWA install tracking
- **`config/urls.py`** - Contains PWA-related URL patterns:
  - `/manifest.json`
  - `/service-worker.js`
  - `/offline/`
  - `/pwa/install/`

#### 3. Templates & Partials
- **`templates/partials/pwa_install_banner.html`** - Installation prompt banner
- **`templates/static_pages/offline.html`** - Offline fallback page
- **`templates/partials/meta_tags.html`** - Contains PWA meta tags (lines 20-32)

#### 4. Static Assets
- **`static/css/pwa.css`** - PWA-specific styles (228 lines)
- **`static/manifest.json`** - PWA manifest file
- **`static/browserconfig.xml`** - Microsoft tile configuration
- **`static/images/favicon_io/`** - PWA icons:
  - `android-chrome-192x192.png`
  - `android-chrome-512x512.png`
  - `apple-touch-icon.png`
  - `favicon-16x16.png`
  - `favicon-32x32.png`
  - `favicon.ico`

#### 5. Documentation
- **`DOCS/archive/13-pwa-implementation.md`** - Complete PWA implementation guide
- **`DOCS/plans/django-i18n-implementation-plan.md`** - Contains PWA translation references

### Cache Versioning Changes

These changes were implemented to fix PWA caching issues:

#### 1. Settings Configuration
- **`config/settings/base.py`** (lines 179-197):
  - `get_cache_version()` function - Uses git commit hash for versioning
  - `CACHE_VERSION` variable - Global cache version setting

#### 2. Context Processor
- **`apps/core/context_processors.py`** (line 17):
  - `CACHE_VERSION` added to template context

#### 3. Template Changes
- **`templates/base.html`**:
  - Line 13: `{% static 'css/mobile.css' %}?v={{ CACHE_VERSION }}`
  - Line 16: `{% static 'css/pwa.css' %}?v={{ CACHE_VERSION }}`
  - Line 146: `{% static 'js/pwa-register.js' %}?v={{ CACHE_VERSION }}`

#### 4. PWA View Updates
- **`apps/core/pwa_views.py`**:
  - Service worker view reads from filesystem (line 96)
  - Added cache control headers

### Integration Points

PWA is integrated in the following locations:

1. **Base Template** (`templates/base.html`):
   - Line 16: PWA CSS file reference
   - Line 146: PWA registration script

2. **Meta Tags** (`templates/partials/meta_tags.html`):
   - Lines 20-32: PWA meta tags (theme-color, apple-mobile-web-app-capable, etc.)
   - Line 32: Manifest link

3. **URL Configuration** (`config/urls.py`):
   - Lines 10-15: PWA view imports
   - Lines 31-36: PWA URL patterns

4. **Context Processors** (`config/settings/base.py`):
   - Listed in TEMPLATES['OPTIONS']['context_processors']

---

## Removal Plan

### Phase 1: Backup Current State

**Before making any changes:**

```bash
# Create a git branch for the removal
git checkout -b remove-pwa-functionality

# Create a backup commit
git add .
git commit -m "Backup before PWA removal"

# Optional: Create a tag for reference
git tag backup-before-pwa-removal
```

### Phase 2: Remove PWA Files

#### Step 2.1: Delete Service Worker Files
```bash
# From project root
Remove-Item -Path "templates\service-worker.js"
Remove-Item -Path "static\js\pwa-register.js"
```

**Files to delete:**
- `templates/service-worker.js`
- `static/js/pwa-register.js`

#### Step 2.2: Delete PWA Templates
```bash
Remove-Item -Path "templates\partials\pwa_install_banner.html"
Remove-Item -Path "templates\static_pages\offline.html"
```

**Files to delete:**
- `templates/partials/pwa_install_banner.html`
- `templates/static_pages/offline.html`

#### Step 2.3: Delete PWA Static Assets
```bash
Remove-Item -Path "static\css\pwa.css"
Remove-Item -Path "static\manifest.json"
Remove-Item -Path "static\browserconfig.xml"
```

**Files to delete:**
- `static/css/pwa.css`
- `static/manifest.json`
- `static/browserconfig.xml`

**Note:** Keep favicon files as they're still useful for browser tabs:
- Keep `static/images/favicon_io/` directory and all icons

#### Step 2.4: Delete PWA Views Module
```bash
Remove-Item -Path "apps\core\pwa_views.py"
```

**Files to delete:**
- `apps/core/pwa_views.py`

### Phase 3: Update Code Files

#### Step 3.1: Update URL Configuration

**File:** `config/urls.py`

Remove PWA imports (lines 10-15):
```python
# REMOVE THESE LINES:
from apps.core.pwa_views import (
    manifest_view,
    service_worker_view,
    offline_view,
    browserconfig_view,
    PWAInstallView
)
```

Remove PWA URL patterns (lines 31-36):
```python
# REMOVE THESE LINES:
    # PWA URLs
    path('manifest.json', manifest_view, name='manifest'),
    path('service-worker.js', service_worker_view, name='service-worker'),
    path('offline/', offline_view, name='offline'),
    path('browserconfig.xml', browserconfig_view, name='browserconfig'),
    path('pwa/install/', PWAInstallView.as_view(), name='pwa-install'),
```

#### Step 3.2: Update Base Template

**File:** `templates/base.html`

Remove PWA CSS reference (line 14-16):
```html
<!-- REMOVE THESE LINES: -->
    <!-- PWA-specific CSS -->
    <link rel="stylesheet" href="{% static 'css/pwa.css' %}?v={{ CACHE_VERSION }}">
```

Remove PWA script registration (line 144-146):
```html
<!-- REMOVE THESE LINES: -->
    <!-- PWA Service Worker Registration -->
    <script src="{% static 'js/pwa-register.js' %}?v={{ CACHE_VERSION }}"></script>
```

#### Step 3.3: Update Meta Tags Template

**File:** `templates/partials/meta_tags.html`

Remove PWA meta tags (lines 20-32):
```html
{# REMOVE THESE LINES: #}
{# PWA Meta Tags #}
<meta name="theme-color" content="#1e4d7b">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="Petição Brasil">
<meta name="mobile-web-app-capable" content="yes">
<meta name="application-name" content="Petição Brasil">
<meta name="msapplication-TileColor" content="#1e4d7b">
<meta name="msapplication-TileImage" content="{% static 'images/favicon_io/android-chrome-192x192.png' %}">
<meta name="msapplication-config" content="{% static 'browserconfig.xml' %}">

{# PWA Links #}
<link rel="manifest" href="/manifest.json">
```

Keep only the cache control meta tags (lines 9-12) - these are useful for preventing HTML caching.

### Phase 4: Reverse Cache Versioning Changes

#### Step 4.1: Remove Cache Version Function

**File:** `config/settings/base.py`

Remove the cache versioning function and variable (lines 179-197):
```python
# REMOVE THESE LINES:
# Cache busting version - automatically uses git commit hash
def get_cache_version():
    """
    Get cache version from git commit hash.
    Falls back to timestamp in development or if git is unavailable.
    """
    try:
        # Get short git commit hash (e.g., 'a3f8c2b')
        git_hash = subprocess.check_output(
            ['git', 'rev-parse', '--short', 'HEAD'],
            cwd=BASE_DIR,
            stderr=subprocess.DEVNULL
        ).decode('ascii').strip()
        return git_hash
    except:
        # Fallback for development or when git is not available
        import time
        return f"dev-{int(time.time())}"

CACHE_VERSION = get_cache_version()
```

Remove the `subprocess` import if it's no longer needed (check line ~6):
```python
# REMOVE THIS LINE IF NOT USED ELSEWHERE:
import subprocess
```

#### Step 4.2: Update Context Processor

**File:** `apps/core/context_processors.py`

Remove CACHE_VERSION from context (line 17):
```python
def site_settings(request):
    """
    Add site-wide settings to template context.
    """
    return {
        'SITE_NAME': settings.SITE_NAME,
        'SITE_URL': settings.SITE_URL,
        'TURNSTILE_SITE_KEY': settings.TURNSTILE_SITE_KEY,
        'TURNSTILE_ENABLED': settings.TURNSTILE_ENABLED,
        # REMOVE THIS LINE:
        # 'CACHE_VERSION': getattr(settings, 'CACHE_VERSION', 'v3.0.0'),
    }
```

Also remove the unused `time` import (line 5) if it exists:
```python
# REMOVE THIS LINE:
# import time
```

#### Step 4.3: Remove Query String Versioning from Templates

**File:** `templates/base.html`

Remove `?v={{ CACHE_VERSION }}` from CSS file (line 13):
```html
<!-- CHANGE FROM: -->
<link rel="stylesheet" href="{% static 'css/mobile.css' %}?v={{ CACHE_VERSION }}">

<!-- CHANGE TO: -->
<link rel="stylesheet" href="{% static 'css/mobile.css' %}">
```

**Note:** The `?v={{ CACHE_VERSION }}` for `pwa.css` and `pwa-register.js` will already be removed when we delete those lines in Phase 3.

### Phase 5: Clean Up Documentation

#### Step 5.1: Update or Remove PWA Documentation

**File:** `DOCS/archive/13-pwa-implementation.md`

Options:
1. **Keep as archive** - Rename to indicate it's no longer active:
   ```bash
   Rename-Item -Path "DOCS\archive\13-pwa-implementation.md" -NewName "REMOVED-13-pwa-implementation.md"
   ```

2. **Delete entirely:**
   ```bash
   Remove-Item -Path "DOCS\archive\13-pwa-implementation.md"
   ```

**Recommendation:** Keep as archive with "REMOVED-" prefix for future reference.

#### Step 5.2: Update i18n Plan

**File:** `DOCS/plans/django-i18n-implementation-plan.md`

Search for PWA references and either:
- Remove sections mentioning PWA translation
- Add notes that PWA has been removed

#### Step 5.3: Create Removal Documentation

Create this file documenting what was removed and why (this document).

### Phase 6: Testing & Validation

#### Step 6.1: Run Local Server

```bash
python manage.py runserver
```

**Expected Results:**
- No 404 errors for `/manifest.json`, `/service-worker.js`, `/offline/`
- CSS loads properly without version query strings
- No JavaScript console errors about service worker
- Site works normally in browser
- No PWA install prompt appears

#### Step 6.2: Check for Errors

```bash
# Check for Python errors
python manage.py check

# Check for missing static files
python manage.py collectstatic --dry-run --noinput
```

#### Step 6.3: Clear Browser Cache & Service Worker

**Manual testing:**
1. Open Chrome DevTools (F12)
2. Go to Application tab
3. Under "Service Workers" - unregister any active service workers
4. Under "Storage" - Clear site data
5. Hard refresh (Ctrl + Shift + R)
6. Verify CSS loads correctly
7. Test in incognito mode
8. Test navigation and page refreshes

#### Step 6.4: Test Key Functionality

- [ ] Home page loads with proper styling
- [ ] List petitions page works
- [ ] Create petition page works
- [ ] Sign petition flow works
- [ ] Account pages work (login, register, profile)
- [ ] Mobile responsive design still works
- [ ] All static assets load (images, CSS)

### Phase 7: Deployment

#### Step 7.1: Commit Changes

```bash
# Stage all changes
git add .

# Review changes
git status
git diff --staged

# Commit
git commit -m "Remove PWA functionality and cache versioning

- Removed service worker and PWA registration
- Deleted PWA views, templates, and static files
- Removed cache versioning query strings
- Cleaned up PWA meta tags and references
- Simplified static asset loading

Reason: PWA added unnecessary complexity and caused persistent
caching issues. Project is a prototype/TCC and doesn't need
full PWA functionality."
```

#### Step 7.2: Push to Repository

```bash
# Push to remote
git push origin remove-pwa-functionality

# Create pull request for review (optional)
# Or merge directly if confident
git checkout main
git merge remove-pwa-functionality
git push origin main
```

#### Step 7.3: Deploy to Heroku

Heroku will automatically deploy when changes are pushed to `main` branch (if automatic deploys are enabled).

**Monitor deployment:**
```bash
heroku logs --tail --app your-app-name
```

#### Step 7.4: Post-Deployment Validation

1. Visit production site
2. Clear service workers in production
3. Test key functionality
4. Monitor for any errors
5. Check that CSS loads properly on first visit and refreshes

---

## Rollback Strategy

If something goes wrong during removal:

### Option 1: Revert Git Commit
```bash
git revert HEAD
git push origin main
```

### Option 2: Restore from Backup Tag
```bash
git checkout backup-before-pwa-removal
git checkout -b restore-pwa
# Review and merge
```

### Option 3: Cherry-Pick Specific Files
```bash
git checkout <previous-commit-hash> -- path/to/file
```

---

## Benefits of Removal

### Immediate Benefits
1. **Simpler codebase** - Less complexity to maintain
2. **Fewer caching issues** - No service worker interference
3. **Faster development** - No cache invalidation concerns
4. **Better debugging** - CSS changes reflect immediately
5. **Reduced file count** - Fewer files to manage

### Long-term Benefits
1. **Easier to understand** for TCC evaluation
2. **Less maintenance burden** for a prototype
3. **Standard Django patterns** - No PWA-specific workarounds
4. **Better suited for scope** - PWA is overkill for a proof-of-concept

---

## What Stays

These features remain after PWA removal:

### ✅ Keep All Core Functionality
- Petition creation and signing
- ICP-Brasil certificate verification
- User authentication
- Email notifications
- PDF generation
- Mobile-responsive design
- All business logic

### ✅ Keep Mobile CSS
- `static/css/mobile.css` - Mobile responsive styles
- Mobile menu functionality
- Touch-friendly interfaces

### ✅ Keep Favicons
- `static/images/favicon_io/` directory
- Browser tab icons
- Bookmark icons

### ✅ Keep Cache Control for HTML
- Meta tags preventing HTML caching
- This is standard practice, not PWA-specific

### ✅ Keep WhiteNoise Configuration
- Static file serving with WhiteNoise
- `CompressedManifestStaticFilesStorage` for file hashing
- This is standard Django production setup

---

## Alternative: Minimal PWA (Optional)

If you want to keep SOME PWA features without the complexity:

### Simplified Approach
1. Keep only `manifest.json` with basic app info
2. Remove service worker entirely
3. Keep PWA meta tags for "Add to Home Screen" on mobile
4. No caching, no offline support

### Files to Keep (Minimal PWA)
- `static/manifest.json` (simplified)
- PWA meta tags in `templates/partials/meta_tags.html`
- PWA icons in `static/images/favicon_io/`

### Files to Remove (Minimal PWA)
- Service worker (all versions)
- PWA registration script
- Offline page
- PWA install banner
- Cache versioning system
- `apps/core/pwa_views.py`

This gives you "Add to Home Screen" functionality on mobile without any caching complexity.

---

## Estimated Timeline

| Phase | Duration | Notes |
|-------|----------|-------|
| Phase 1: Backup | 5 minutes | Create branch and backup |
| Phase 2: Delete Files | 10 minutes | Remove PWA files |
| Phase 3: Update Code | 30 minutes | Modify templates and configs |
| Phase 4: Reverse Cache Versioning | 20 minutes | Remove versioning code |
| Phase 5: Clean Documentation | 15 minutes | Update docs |
| Phase 6: Testing | 30 minutes | Thorough local testing |
| Phase 7: Deployment | 20 minutes | Git commit and deploy |
| **Total** | **~2.5 hours** | Conservative estimate |

---

## Checklist

Use this checklist to track progress:

### Pre-Removal
- [ ] Create backup branch `remove-pwa-functionality`
- [ ] Create backup commit
- [ ] Create backup tag (optional)
- [ ] Review current PWA functionality

### File Deletion
- [ ] Delete `templates/service-worker.js`
- [ ] Delete `static/js/pwa-register.js`
- [ ] Delete `templates/partials/pwa_install_banner.html`
- [ ] Delete `templates/static_pages/offline.html`
- [ ] Delete `static/css/pwa.css`
- [ ] Delete `static/manifest.json`
- [ ] Delete `static/browserconfig.xml`
- [ ] Delete `apps/core/pwa_views.py`

### Code Updates
- [ ] Remove PWA imports from `config/urls.py`
- [ ] Remove PWA URL patterns from `config/urls.py`
- [ ] Remove PWA CSS from `templates/base.html`
- [ ] Remove PWA script from `templates/base.html`
- [ ] Remove PWA meta tags from `templates/partials/meta_tags.html`
- [ ] Remove `get_cache_version()` from `config/settings/base.py`
- [ ] Remove `CACHE_VERSION` from `config/settings/base.py`
- [ ] Remove `subprocess` import if unused
- [ ] Remove `CACHE_VERSION` from `apps/core/context_processors.py`
- [ ] Remove `time` import if unused from context processor
- [ ] Remove `?v={{ CACHE_VERSION }}` from mobile.css in base.html

### Documentation
- [ ] Rename or mark `DOCS/archive/13-pwa-implementation.md`
- [ ] Update `DOCS/plans/django-i18n-implementation-plan.md`
- [ ] Keep this removal plan for reference

### Testing
- [ ] Run `python manage.py check`
- [ ] Run `python manage.py collectstatic --dry-run`
- [ ] Test local server
- [ ] Clear browser service workers
- [ ] Test in incognito mode
- [ ] Test all key pages
- [ ] Test mobile responsiveness
- [ ] Verify CSS loads correctly

### Deployment
- [ ] Commit changes with descriptive message
- [ ] Push to repository
- [ ] Deploy to production
- [ ] Monitor deployment logs
- [ ] Validate production site
- [ ] Clear production service workers
- [ ] Final production testing

---

## Questions & Answers

### Q: Will removing PWA affect mobile users?
**A:** No. The mobile-responsive design is separate from PWA functionality. Users will still have a great mobile experience, they just won't be able to "install" the app or use it offline.

### Q: What about offline functionality?
**A:** This is a web-based petition platform that requires internet for signature verification and submission. Offline functionality wasn't essential and added complexity.

### Q: Should we keep the manifest.json?
**A:** Not necessary for this project. If you want "Add to Home Screen" on mobile, you can keep a minimal manifest, but remove all service worker references.

### Q: Will this affect SEO or performance?
**A:** No negative impact. PWA features don't significantly affect SEO. Static file serving with WhiteNoise remains, which is good for performance.

### Q: Can we re-add PWA later?
**A:** Yes. The backup tag and documentation remain. If the project becomes production-ready in the future, PWA can be re-implemented with better planning.

### Q: What about browser caching of CSS?
**A:** Django's `ManifestStaticFilesStorage` (via WhiteNoise) handles this automatically by adding content hashes to filenames during `collectstatic`. This is more reliable than query string versioning.

---

## Conclusion

This removal plan provides a comprehensive approach to simplifying the Petição Brasil project by:
1. Removing unnecessary PWA complexity
2. Reverting problematic cache versioning attempts
3. Returning to standard Django patterns
4. Maintaining all core functionality

The project will be simpler to maintain, easier to understand for TCC evaluation, and free from the persistent caching issues that plagued the PWA implementation.

**Final Recommendation:** Proceed with full PWA removal. The added complexity doesn't justify the benefits for a prototype/TCC project.

---

## References

- Django Static Files Documentation: https://docs.djangoproject.com/en/5.1/howto/static-files/
- WhiteNoise Documentation: http://whitenoise.evans.io/
- Original PWA Implementation: `DOCS/archive/13-pwa-implementation.md`
- Git Backup Tag: `backup-before-pwa-removal`

**Document Version:** 1.0  
**Last Updated:** January 27, 2026  
**Author:** Analysis of current PWA implementation
