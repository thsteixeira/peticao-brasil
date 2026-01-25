# PWA Implementation Guide for Petição Brasil

## Overview
This project now includes a complete Progressive Web App (PWA) implementation that provides:
- Offline functionality
- App-like experience on mobile devices
- Push notifications support
- Install prompt
- Fast loading with caching strategies
- Automatic updates

## What Was Implemented

### 1. Core PWA Files

#### Manifest File (`/manifest.json`)
- Defines app metadata (name, icons, colors, etc.)
- Configures display mode as "standalone" for app-like experience
- Includes app shortcuts for quick actions
- Available at: `/manifest.json`

#### Service Worker (`/service-worker.js`)
- Implements caching strategies:
  - **Cache First**: For static assets (CSS, JS, images)
  - **Network First**: For dynamic content (petitions, user data)
  - **Network Only**: For admin and API calls
- Provides offline fallback
- Supports background sync
- Handles push notifications
- Available at: `/service-worker.js`

#### Offline Page (`/offline/`)
- Beautiful offline fallback page
- Auto-reconnects when connection is restored
- Shows helpful tips for reconnecting

### 2. PWA Assets

#### Icons
- Created SVG template at `static/images/icons/icon-512x512.svg`
- Required PNG sizes: 72x72, 96x96, 128x128, 144x144, 152x152, 192x192, 384x384, 512x512
- See `static/images/icons/README.md` for generation instructions

#### Styles
- `static/css/pwa.css`: PWA-specific styles
- Safe area support for notched devices
- Offline content indicators
- Network status badges

### 3. Django Integration

#### Views (`apps/core/pwa_views.py`)
- `manifest_view`: Serves dynamic manifest.json
- `service_worker_view`: Serves service worker
- `offline_view`: Renders offline page
- `browserconfig_view`: Serves Microsoft browser config
- `PWAInstallView`: Tracks installations

#### URLs
Added to `config/urls.py`:
- `/manifest.json`
- `/service-worker.js`
- `/offline/`
- `/browserconfig.xml`
- `/pwa/install/`

### 4. Frontend Components

#### Service Worker Registration (`static/js/pwa-register.js`)
- Automatically registers service worker
- Handles updates and shows notification
- Manages install prompt
- Tracks online/offline status
- Provides PWA utilities

#### Install Banner (`templates/partials/pwa_install_banner.html`)
- Beautiful install prompt
- Shows benefits of installing
- Smart dismissal (shows again after 7 days)
- Tracks user interactions

#### Meta Tags (`templates/partials/meta_tags.html`)
Updated with:
- PWA meta tags
- Theme color
- Apple touch icon
- Manifest link
- iOS-specific meta tags

## How to Complete Setup

### Step 1: Generate Icons
You need to generate PNG icons from the SVG template:

**Option A: Using ImageMagick (Windows)**
```powershell
# Install ImageMagick first if you don't have it
# Download from: https://imagemagick.org/script/download.php#windows

cd static/images/icons

magick icon-512x512.svg -resize 72x72 icon-72x72.png
magick icon-512x512.svg -resize 96x96 icon-96x96.png
magick icon-512x512.svg -resize 128x128 icon-128x128.png
magick icon-512x512.svg -resize 144x144 icon-144x144.png
magick icon-512x512.svg -resize 152x152 icon-152x152.png
magick icon-512x512.svg -resize 192x192 icon-192x192.png
magick icon-512x512.svg -resize 384x384 icon-384x384.png
magick icon-512x512.svg -resize 512x512 icon-512x512.png
magick icon-512x512.svg -resize 180x180 apple-touch-icon.png
```

**Option B: Online Tool**
1. Go to https://realfavicongenerator.net/ or https://www.pwabuilder.com/imageGenerator
2. Upload `static/images/icons/icon-512x512.svg`
3. Download generated icons
4. Place in `static/images/icons/`

**Option C: Manual Creation**
Use any image editor (Photoshop, GIMP, Figma) to create icons in required sizes.

### Step 2: Collect Static Files
```bash
python manage.py collectstatic --noreload
```

### Step 3: Test Locally

1. **Run with HTTPS** (PWA requires HTTPS):
```bash
# Using Django development server with SSL (requires django-extensions)
pip install django-extensions werkzeug pyOpenSSL
python manage.py runserver_plus --cert-file cert.pem
```

Or use a tunnel service:
```bash
# Using ngrok
ngrok http 8000
```

2. **Test PWA Features**:
   - Open in Chrome/Edge
   - Open DevTools > Application > Manifest
   - Check Service Workers tab
   - Try going offline (DevTools > Network > Offline)
   - Look for install prompt

### Step 4: Lighthouse Audit
```bash
# Install Lighthouse CLI
npm install -g lighthouse

# Run PWA audit
lighthouse https://your-site.com --view --preset=desktop
```

## Testing Checklist

- [ ] Icons generated in all required sizes
- [ ] Manifest.json loads correctly
- [ ] Service worker registers successfully
- [ ] Offline page displays when disconnected
- [ ] Install prompt appears (on supported browsers)
- [ ] App can be installed to home screen
- [ ] App works offline after installation
- [ ] Updates are detected and user is notified
- [ ] Lighthouse PWA score > 90

## Browser Support

### ✅ Full Support
- Chrome/Edge 84+
- Safari 11.1+ (iOS)
- Firefox 79+
- Samsung Internet 12+

### ⚠️ Partial Support
- Safari (macOS) - No install prompt, but works as PWA
- Firefox - Limited install prompt support

### ❌ No Support
- Internet Explorer
- Older browsers

## Features by Platform

### Android
- Full PWA support
- Install prompt
- Push notifications
- Background sync
- Share target

### iOS
- Standalone mode
- Limited push notifications (iOS 16.4+)
- Add to home screen (manual)
- No background sync

### Desktop
- Install to taskbar/dock
- Standalone window
- All features except mobile-specific ones

## Performance Optimizations

### Caching Strategy
```javascript
// Static assets: Cache First (1 year)
/static/* → Cache → Network

// Dynamic content: Network First
/peticoes/* → Network → Cache

// Admin: Network Only
/admin/* → Network
```

### Offline Capabilities
- View previously visited petitions
- Browse cached content
- Read documentation
- Auto-sync when online

### Update Strategy
- Check for updates every hour
- Show notification when update available
- User can choose when to update
- Automatic activation on next visit

## Monitoring and Analytics

### Track PWA Metrics
The implementation includes tracking for:
- Install events
- Install prompt interactions
- Offline usage
- Service worker updates

### Add Analytics (Optional)
```javascript
// Example with Google Analytics
gtag('event', 'pwa_install', {
  event_category: 'PWA',
  event_label: 'User installed PWA'
});
```

## Troubleshooting

### Service Worker Not Registering
1. Check browser console for errors
2. Ensure HTTPS is enabled
3. Verify service-worker.js is accessible
4. Check scope configuration

### Install Prompt Not Showing
1. Must be served over HTTPS
2. Must have valid manifest.json
3. Must have service worker
4. User must visit site at least twice
5. User must interact with page (click, etc.)

### Offline Page Not Working
1. Check service worker registration
2. Verify offline.html is cached
3. Check network tab in DevTools
4. Ensure proper cache strategy

### Icons Not Displaying
1. Generate all required icon sizes
2. Run collectstatic
3. Check manifest.json paths
4. Clear browser cache

## Next Steps

### Recommended Enhancements
1. **Push Notifications**: Implement server-side push
2. **Background Sync**: Queue actions when offline
3. **Share Target**: Allow sharing to your app
4. **Periodic Background Sync**: Update content in background
5. **App Shortcuts**: Add more quick actions
6. **Screenshots**: Add app screenshots to manifest

### Advanced Features
1. **IndexedDB**: Store petition data locally
2. **Web Share API**: Better sharing integration
3. **Credential Management**: Store login credentials
4. **Payment Request**: For donations
5. **Contact Picker**: Better UX for sharing

## Resources

- [MDN PWA Guide](https://developer.mozilla.org/en-US/docs/Web/Progressive_web_apps)
- [web.dev PWA](https://web.dev/progressive-web-apps/)
- [PWA Builder](https://www.pwabuilder.com/)
- [Workbox](https://developers.google.com/web/tools/workbox) - Google's PWA toolkit

## Security Considerations

1. **HTTPS Required**: PWA only works over HTTPS
2. **CSP Headers**: Ensure Content Security Policy allows service workers
3. **Scope**: Service worker scope is limited to its directory
4. **Cache Hygiene**: Regularly clear old caches
5. **Sensitive Data**: Never cache sensitive user data

## Deployment Notes

### Production Checklist
- [ ] Generate production icons
- [ ] Configure HTTPS/SSL
- [ ] Set correct SITE_URL in settings
- [ ] Enable cache headers
- [ ] Test on multiple devices
- [ ] Monitor error logs
- [ ] Set up analytics
- [ ] Create app store listings (optional)

### Environment Variables
No additional environment variables needed. Uses existing:
- `SITE_NAME`
- `SITE_URL`
- `STATIC_URL`

## Support

For issues or questions:
1. Check browser console for errors
2. Review service worker logs
3. Use Lighthouse for diagnostics
4. Test on multiple browsers/devices

---

**Congratulations! Your Django app is now a Progressive Web App! 🎉**
