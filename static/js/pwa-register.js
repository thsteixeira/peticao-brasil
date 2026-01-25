// PWA Registration and Installation Handler
// Petição Brasil - Progressive Web App

(function() {
    'use strict';
    
    // Check if service workers are supported
    if (!('serviceWorker' in navigator)) {
        console.warn('Service Workers are not supported in this browser');
        return;
    }
    
    // Configuration
    const config = {
        serviceWorkerUrl: '/service-worker.js',
        scope: '/',
        updateInterval: 60 * 60 * 1000, // Check for updates every hour
    };
    
    let deferredPrompt = null;
    let swRegistration = null;
    
    // Register Service Worker
    async function registerServiceWorker() {
        try {
            swRegistration = await navigator.serviceWorker.register(config.serviceWorkerUrl, {
                scope: config.scope
            });
            
            console.log('[PWA] Service Worker registered successfully:', swRegistration.scope);
            
            // Check for updates periodically
            setInterval(() => {
                swRegistration.update();
            }, config.updateInterval);
            
            // Handle service worker updates
            swRegistration.addEventListener('updatefound', () => {
                const newWorker = swRegistration.installing;
                
                newWorker.addEventListener('statechange', () => {
                    if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                        // New service worker available
                        showUpdateNotification();
                    }
                });
            });
            
        } catch (error) {
            console.error('[PWA] Service Worker registration failed:', error);
        }
    }
    
    // Show update notification
    function showUpdateNotification() {
        const notification = document.createElement('div');
        notification.id = 'pwa-update-notification';
        notification.className = 'fixed bottom-4 left-4 right-4 md:left-auto md:right-4 md:w-96 bg-blue-600 text-white p-4 rounded-lg shadow-lg z-50 transform transition-transform';
        notification.innerHTML = `
            <div class="flex items-start">
                <div class="flex-shrink-0">
                    <svg class="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                    </svg>
                </div>
                <div class="ml-3 flex-1">
                    <h3 class="font-semibold">Nova versão disponível!</h3>
                    <p class="text-sm mt-1">Uma atualização do aplicativo está pronta.</p>
                    <div class="mt-3 flex gap-2">
                        <button id="pwa-update-btn" class="bg-white text-blue-600 px-4 py-2 rounded font-semibold text-sm hover:bg-blue-50">
                            Atualizar Agora
                        </button>
                        <button id="pwa-dismiss-btn" class="border border-white px-4 py-2 rounded text-sm hover:bg-blue-700">
                            Depois
                        </button>
                    </div>
                </div>
                <button id="pwa-close-btn" class="ml-3 flex-shrink-0">
                    <svg class="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"></path>
                    </svg>
                </button>
            </div>
        `;
        
        document.body.appendChild(notification);
        
        // Add event listeners
        document.getElementById('pwa-update-btn').addEventListener('click', () => {
            if (swRegistration && swRegistration.waiting) {
                swRegistration.waiting.postMessage({ type: 'SKIP_WAITING' });
                window.location.reload();
            }
        });
        
        document.getElementById('pwa-dismiss-btn').addEventListener('click', () => {
            notification.remove();
        });
        
        document.getElementById('pwa-close-btn').addEventListener('click', () => {
            notification.remove();
        });
    }
    
    // Handle install prompt
    window.addEventListener('beforeinstallprompt', (e) => {
        // Prevent Chrome 67 and earlier from automatically showing the prompt
        e.preventDefault();
        
        // Stash the event so it can be triggered later
        deferredPrompt = e;
        
        console.log('[PWA] Install prompt available');
        
        // Show custom install button
        showInstallButton();
    });
    
    // Show install button in footer
    function showInstallButton() {
        const installLink = document.getElementById('pwa-install-link');
        if (!installLink) {
            return;
        }
        
        // Don't show if already installed
        if (window.matchMedia('(display-mode: standalone)').matches) {
            console.log('[PWA] App is already installed');
            return;
        }
        
        // Show the link
        installLink.classList.remove('hidden');
        
        // Add click handler
        installLink.addEventListener('click', async () => {
            if (!deferredPrompt) {
                console.log('[PWA] No install prompt available');
                return;
            }
            
            // Show the install prompt
            deferredPrompt.prompt();
            
            // Wait for the user to respond to the prompt
            const { outcome } = await deferredPrompt.userChoice;
            console.log(`[PWA] User response to install prompt: ${outcome}`);
            
            // Clear the deferred prompt
            deferredPrompt = null;
            
            // Hide the link
            installLink.classList.add('hidden');
        });
    }
    
    // Track installation
    window.addEventListener('appinstalled', () => {
        console.log('[PWA] App was installed successfully');
        
        // Hide install link if exists
        const installLink = document.getElementById('pwa-install-link');
        if (installLink) {
            installLink.classList.add('hidden');
        }
        
        // Track installation analytics (if you have analytics)
        if (typeof gtag !== 'undefined') {
            gtag('event', 'pwa_install', {
                event_category: 'PWA',
                event_label: 'App Installed'
            });
        }
    });
    
    // Detect if app is running as PWA
    function isPWA() {
        return window.matchMedia('(display-mode: standalone)').matches ||
               window.navigator.standalone === true;
    }
    
    // Add PWA class to body if running as PWA
    if (isPWA()) {
        document.documentElement.classList.add('pwa-mode');
        console.log('[PWA] Running in standalone mode');
    }
    
    // Handle online/offline status
    function updateOnlineStatus() {
        const status = navigator.onLine ? 'online' : 'offline';
        document.body.setAttribute('data-network-status', status);
        
        if (status === 'offline') {
            showOfflineNotification();
        }
    }
    
    // Show offline notification
    function showOfflineNotification() {
        // Don't show if already exists
        if (document.getElementById('offline-notification')) {
            return;
        }
        
        const notification = document.createElement('div');
        notification.id = 'offline-notification';
        notification.className = 'fixed top-4 left-4 right-4 md:left-auto md:right-4 md:w-96 bg-yellow-500 text-white p-4 rounded-lg shadow-lg z-50';
        notification.innerHTML = `
            <div class="flex items-center">
                <svg class="h-6 w-6 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M18.364 5.636a9 9 0 010 12.728m0 0l-2.829-2.829m2.829 2.829L21 21M15.536 8.464a5 5 0 010 7.072m0 0l-2.829-2.829m-4.243 2.829a4.978 4.978 0 01-1.414-2.83m-1.414 5.658a9 9 0 01-2.167-9.238m7.824 2.167a1 1 0 111.414 1.414m-1.414-1.414L3 3m8.293 8.293l1.414 1.414"></path>
                </svg>
                <div>
                    <p class="font-semibold">Você está offline</p>
                    <p class="text-sm">Algumas funcionalidades podem estar limitadas</p>
                </div>
            </div>
        `;
        
        document.body.appendChild(notification);
    }
    
    // Remove offline notification when back online
    window.addEventListener('online', () => {
        const notification = document.getElementById('offline-notification');
        if (notification) {
            notification.remove();
        }
        updateOnlineStatus();
    });
    
    window.addEventListener('offline', updateOnlineStatus);
    
    // Initialize
    window.addEventListener('load', () => {
        registerServiceWorker();
        updateOnlineStatus();
    });
    
    // Expose PWA utilities globally
    window.PWA = {
        isInstalled: isPWA,
        showInstallPrompt: () => {
            if (deferredPrompt) {
                deferredPrompt.prompt();
            } else {
                console.log('[PWA] No install prompt available');
            }
        },
        checkForUpdates: () => {
            if (swRegistration) {
                swRegistration.update();
            }
        }
    };
    
})();
