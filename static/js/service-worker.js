// Service Worker for Petição Brasil PWA
// IMPORTANT: Update this version on every deploy to invalidate old caches
// Last updated: 2025-01-24
const CACHE_VERSION = 'v1.0.2-20250124';
const CACHE_NAME = `peticao-brasil-${CACHE_VERSION}`;
const OFFLINE_URL = '/offline/';

// Files to cache immediately on install
const STATIC_CACHE_URLS = [
  '/',
  '/offline/',
  // Don't pre-cache CSS files - let them be cached on first request
  // This prevents caching old versions
  '/static/manifest.json',
];

// Dynamic cache configuration
const CACHE_STRATEGIES = {
  // Network first for CSS to always get latest styles (with fallback to cache when offline)
  networkFirst: [
    '/static/css/',
    '/static/js/pwa',
    '/static/js/share',
  ],
  // Cache first for truly static assets (images, fonts)
  static: [
    '/static/images/',
    '/static/fonts/',
    '/media/',
  ],
  // Network first, fallback to cache
  dynamic: [
    '/peticoes/',
    '/accounts/',
    '/signatures/',
  ],
  // Network only (don't cache)
  networkOnly: [
    '/admin/',
    '/api/',
    'chrome-extension://',
  ]
};

// Install event - cache essential files
self.addEventListener('install', (event) => {
  console.log('[Service Worker] Installing Service Worker...', event);
  
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      console.log('[Service Worker] Caching static resources');
      return cache.addAll(STATIC_CACHE_URLS.map(url => new Request(url, { cache: 'reload' })));
    }).catch((error) => {
      console.error('[Service Worker] Failed to cache static resources:', error);
    })
  );
  
  // Force the waiting service worker to become the active service worker
  self.skipWaiting();
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
  console.log('[Service Worker] Activating Service Worker...', event);
  
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName !== CACHE_NAME) {
            console.log('[Service Worker] Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
  
  // Take control of all pages immediately
  return self.clients.claim();
});

// Fetch event - implement caching strategies
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);
  
  // Skip non-GET requests
  if (request.method !== 'GET') {
    return;
  }
  
  // Skip chrome extensions and other protocols
  if (!url.protocol.startsWith('http')) {
    return;
  }
  Network first for CSS and dynamic JS
  if (shouldUseNetworkFirst(url.pathname)) {
    event.respondWith(networkFirst(request));
    return;
  }
  
  // Static resources - Cache First strategy (images, fonts)
  // Network only strategy for specific paths
  if (shouldUseNetworkOnly(url.pathname)) {
    event.respondWith(fetch(request));
    return;
  }
  
  // Static resources - Cache First strategy
  if (shouldUseCacheFirst(url.pathname)) {
    event.respondWith(cacheFirst(request));
    return;
  }
  
  // Dynamic content - Network First strategy
  event.respondWith(networkFirst(request));
});
network-first strategy
function shouldUseNetworkFirst(pathname) {
  return CACHE_STRATEGIES.networkFirst.some(pattern => pathname.startsWith(pattern));
}

// Check if URL should use 
// Check if URL should use network-only strategy
function shouldUseNetworkOnly(pathname) {
  return CACHE_STRATEGIES.networkOnly.some(pattern => pathname.startsWith(pattern));
}

// Check if URL should use cache-first strategy
function shouldUseCacheFirst(pathname) {
  return CACHE_STRATEGIES.static.some(pattern => pathname.startsWith(pattern));
}

// Cache First Strategy - good for static assets
async function cacheFirst(request) {
  try {
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }
    
    const networkResponse = await fetch(request);
    
    // Cache successful responses
    if (networkResponse && networkResponse.status === 200) {
      const cache = await caches.open(CACHE_NAME);
      cache.put(request, networkResponse.clone());
    }
    
    return networkResponse;
  } catch (error) {
    console.error('[Service Worker] Cache First failed:', error);
    
    // Return offline page for navigation requests
    if (request.mode === 'navigate') {
      const cache = await caches.open(CACHE_NAME);
      return cache.match(OFFLINE_URL);
    }
    
    throw error;
  }
}

// Network First Strategy - good for dynamic content
async function networkFirst(request) {
  try {
    const networkResponse = await fetch(request);
    
    // Cache successful responses
    if (networkResponse && networkResponse.status === 200) {
      const cache = await caches.open(CACHE_NAME);
      cache.put(request, networkResponse.clone());
    }
    
    return networkResponse;
  } catch (error) {
    console.error('[Service Worker] Network First failed, trying cache:', error);
    
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }
    
    // Return offline page for navigation requests
    if (request.mode === 'navigate') {
      const cache = await caches.open(CACHE_NAME);
      return cache.match(OFFLINE_URL);
    }
    
    throw error;
  }
}

// Background Sync for offline form submissions
self.addEventListener('sync', (event) => {
  console.log('[Service Worker] Background sync triggered:', event.tag);
  
  if (event.tag === 'sync-signatures') {
    event.waitUntil(syncSignatures());
  }
});

async function syncSignatures() {
  // This would sync any pending signatures when back online
  console.log('[Service Worker] Syncing signatures...');
  // Implementation would depend on IndexedDB storage of pending actions
}

// Push notifications support
self.addEventListener('push', (event) => {
  console.log('[Service Worker] Push notification received:', event);
  
  const options = {
    body: event.data ? event.data.text() : 'Nova atualização disponível',
    icon: '/static/images/favicon_io/android-chrome-192x192.png',
    badge: '/static/images/favicon_io/favicon-32x32.png',
    vibrate: [200, 100, 200],
    data: {
      dateOfArrival: Date.now(),
      primaryKey: 1
    },
    actions: [
      {
        action: 'explore',
        title: 'Ver Detalhes',
        icon: '/static/images/favicon_io/favicon-32x32.png'
      },
      {
        action: 'close',
        title: 'Fechar',
        icon: '/static/images/favicon_io/favicon-32x32.png'
      }
    ]
  };
  
  event.waitUntil(
    self.registration.showNotification('Petição Brasil', options)
  );
});

// Notification click handler
self.addEventListener('notificationclick', (event) => {
  console.log('[Service Worker] Notification clicked:', event.action);
  
  event.notification.close();
  
  if (event.action === 'explore') {
    event.waitUntil(
      clients.openWindow('/')
    );
  }
});

// Message handler for communication with the main thread
self.addEventListener('message', (event) => {
  console.log('[Service Worker] Message received:', event.data);
  
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
  
  if (event.data && event.data.type === 'CLEAR_CACHE') {
    event.waitUntil(
      caches.keys().then((cacheNames) => {
        return Promise.all(
          cacheNames.map((cacheName) => caches.delete(cacheName))
        );
      })
    );
  }
});

console.log('[Service Worker] Service Worker loaded successfully');
