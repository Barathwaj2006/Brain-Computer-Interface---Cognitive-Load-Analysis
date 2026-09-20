/**
 * NEUROSIM : Progressive Web App (PWA) Service Worker
 * Version: 2.5.5-PRODUCTION
 * Caching Strategy:
 *  - Static Assets (HTML, CSS, JS, SVG, JSON): Cache-First with Network Revalidation
 *  - API Gateway & WebSocket endpoints (/api/..., ws://): Network-Only
 */

const CACHE_NAME = 'neurosim-pwa-v2.5.5';

const STATIC_ASSETS = [
    '/',
    '/index.html',
    '/styles.css',
    '/app.js',
    '/pdf_export.js',
    '/manifest.json',
    '/favicon.svg',
    '/og_preview.svg',
    '/privacy.html',
    '/terms.html',
    '/404.html',
    '/ai_report_model_weights.json'
];

// Install Event: Pre-cache core clinical application shell
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            console.log('[ServiceWorker] Pre-caching offline workstation shell');
            return cache.addAll(STATIC_ASSETS);
        }).then(() => self.skipWaiting())
    );
});

// Activate Event: Purge legacy caches
self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames.map((name) => {
                    if (name !== CACHE_NAME && name.startsWith('neurosim-')) {
                        console.log('[ServiceWorker] Purging legacy cache:', name);
                        return caches.delete(name);
                    }
                })
            );
        }).then(() => self.clients.claim())
    );
});

// Fetch Event: Cache-First for static assets, Network-Only for dynamic API routes
self.addEventListener('fetch', (event) => {
    const requestUrl = new URL(event.request.url);

    // Bypass caching for cross-origin requests, REST API calls, and WebSocket connections
    if (requestUrl.origin !== self.location.origin || requestUrl.pathname.startsWith('/api/') || requestUrl.pathname.startsWith('/ws')) {
        return;
    }

    event.respondWith(
        caches.match(event.request).then((cachedResponse) => {
            if (cachedResponse) {
                // Fetch in background to update cache (stale-while-revalidate)
                fetch(event.request).then((networkResponse) => {
                    if (networkResponse && networkResponse.status === 200) {
                        caches.open(CACHE_NAME).then((cache) => {
                            cache.put(event.request, networkResponse.clone());
                        });
                    }
                }).catch(() => {
                    // Network unavailable; offline mode active
                });
                return cachedResponse;
            }

            return fetch(event.request).then((networkResponse) => {
                if (!networkResponse || networkResponse.status !== 200 || networkResponse.type !== 'basic') {
                    return networkResponse;
                }
                const responseToCache = networkResponse.clone();
                caches.open(CACHE_NAME).then((cache) => {
                    cache.put(event.request, responseToCache);
                });
                return networkResponse;
            }).catch(() => {
                // Return cached index.html for navigation requests when offline
                if (event.request.mode === 'navigate') {
                    return caches.match('/index.html');
                }
            });
        })
    );
});
