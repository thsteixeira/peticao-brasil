/**
 * Share functionality for Petição Brasil
 * Handles petition sharing with Web Share API fallback to custom share menu
 */

class PetitionShare {
    constructor(petitionUuid, petitionTitle, petitionUrl) {
        this.petitionUuid = petitionUuid;
        this.petitionTitle = petitionTitle;
        this.petitionUrl = petitionUrl;
        this.shareButton = null;
        this.shareMenu = null;
    }

    /**
     * Initialize share functionality
     */
    init() {
        this.shareButton = document.getElementById('share-button');
        if (!this.shareButton) {
            console.error('Share button not found');
            return;
        }

        this.shareButton.addEventListener('click', (e) => {
            e.preventDefault();
            this.handleShare();
        });

        // Close menu when clicking outside
        document.addEventListener('click', (e) => {
            if (this.shareMenu && !this.shareButton.contains(e.target) && !this.shareMenu.contains(e.target)) {
                this.closeShareMenu();
            }
        });

        // Close menu on ESC key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.shareMenu) {
                this.closeShareMenu();
            }
        });
    }

    /**
     * Handle share button click
     */
    async handleShare() {
        // Try native Web Share API first (mobile devices)
        if (navigator.share) {
            try {
                await navigator.share({
                    title: this.petitionTitle,
                    text: `${this.petitionTitle} - Petição Brasil`,
                    url: this.petitionUrl
                });
                
                // Track share
                this.trackShare();
                return;
            } catch (err) {
                // User cancelled or error - show custom menu
                if (err.name !== 'AbortError') {
                    console.error('Error sharing:', err);
                }
            }
        }

        // Fallback to custom share menu
        this.showShareMenu();
    }

    /**
     * Show custom share menu
     */
    async showShareMenu() {
        // If menu already exists, toggle it
        if (this.shareMenu) {
            this.closeShareMenu();
            return;
        }

        // Get share URLs from backend
        const shareData = await this.getShareUrls();
        if (!shareData) {
            alert('Erro ao carregar opções de compartilhamento');
            return;
        }

        // Create share menu
        this.shareMenu = document.createElement('div');
        this.shareMenu.id = 'share-menu';
        this.shareMenu.className = 'absolute top-full right-0 mt-2 w-64 bg-white rounded-lg shadow-xl border border-gray-200 z-50 overflow-hidden';
        this.shareMenu.style.animation = 'fadeIn 0.2s ease-out';

        this.shareMenu.innerHTML = `
            <div class="p-3 border-b border-gray-200 bg-gray-50">
                <h3 class="font-semibold text-gray-900">Compartilhar Petição</h3>
            </div>
            <div class="py-2">
                <button class="share-option w-full px-4 py-3 hover:bg-gray-50 flex items-center space-x-3 transition-colors" data-platform="whatsapp" data-url="${shareData.share_urls.whatsapp}">
                    <svg class="w-5 h-5 text-green-600" fill="currentColor" viewBox="0 0 24 24">
                        <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/>
                    </svg>
                    <span class="text-gray-700">WhatsApp</span>
                </button>
                <button class="share-option w-full px-4 py-3 hover:bg-gray-50 flex items-center space-x-3 transition-colors" data-platform="twitter" data-url="${shareData.share_urls.twitter}">
                    <svg class="w-5 h-5 text-blue-400" fill="currentColor" viewBox="0 0 24 24">
                        <path d="M23.953 4.57a10 10 0 01-2.825.775 4.958 4.958 0 002.163-2.723c-.951.555-2.005.959-3.127 1.184a4.92 4.92 0 00-8.384 4.482C7.69 8.095 4.067 6.13 1.64 3.162a4.822 4.822 0 00-.666 2.475c0 1.71.87 3.213 2.188 4.096a4.904 4.904 0 01-2.228-.616v.06a4.923 4.923 0 003.946 4.827 4.996 4.996 0 01-2.212.085 4.936 4.936 0 004.604 3.417 9.867 9.867 0 01-6.102 2.105c-.39 0-.779-.023-1.17-.067a13.995 13.995 0 007.557 2.209c9.053 0 13.998-7.496 13.998-13.985 0-.21 0-.42-.015-.63A9.935 9.935 0 0024 4.59z"/>
                    </svg>
                    <span class="text-gray-700">Twitter / X</span>
                </button>
                <button class="share-option w-full px-4 py-3 hover:bg-gray-50 flex items-center space-x-3 transition-colors" data-platform="facebook" data-url="${shareData.share_urls.facebook}">
                    <svg class="w-5 h-5 text-blue-600" fill="currentColor" viewBox="0 0 24 24">
                        <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/>
                    </svg>
                    <span class="text-gray-700">Facebook</span>
                </button>
                <button class="share-option w-full px-4 py-3 hover:bg-gray-50 flex items-center space-x-3 transition-colors" data-platform="email" data-url="${shareData.share_urls.email}">
                    <svg class="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"/>
                    </svg>
                    <span class="text-gray-700">Email</span>
                </button>
                <button class="share-option w-full px-4 py-3 hover:bg-gray-50 flex items-center space-x-3 transition-colors border-t border-gray-200" data-platform="copy" data-url="${shareData.share_urls.url}">
                    <svg class="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-1M8 5a2 2 0 002 2h2a2 2 0 002-2M8 5a2 2 0 012-2h2a2 2 0 012 2m0 0h2a2 2 0 012 2v3m2 4H10m0 0l3-3m-3 3l3 3"/>
                    </svg>
                    <span class="text-gray-700">Copiar Link</span>
                </button>
            </div>
        `;

        // Add event listeners to share options
        const shareOptions = this.shareMenu.querySelectorAll('.share-option');
        shareOptions.forEach(option => {
            option.addEventListener('click', (e) => {
                e.preventDefault();
                const platform = option.dataset.platform;
                const url = option.dataset.url;
                this.shareOn(platform, url);
            });
        });

        // Position menu relative to button
        this.shareButton.style.position = 'relative';
        this.shareButton.appendChild(this.shareMenu);
    }

    /**
     * Share on specific platform
     */
    shareOn(platform, url) {
        if (platform === 'copy') {
            // Copy to clipboard
            navigator.clipboard.writeText(url).then(() => {
                this.showNotification('Link copiado!');
                this.closeShareMenu();
            }).catch(err => {
                console.error('Failed to copy:', err);
                // Fallback for older browsers
                const input = document.createElement('input');
                input.value = url;
                document.body.appendChild(input);
                input.select();
                document.execCommand('copy');
                document.body.removeChild(input);
                this.showNotification('Link copiado!');
                this.closeShareMenu();
            });
        } else {
            // Open in new window
            window.open(url, '_blank', 'width=600,height=400');
            this.closeShareMenu();
        }
    }

    /**
     * Close share menu
     */
    closeShareMenu() {
        if (this.shareMenu) {
            this.shareMenu.remove();
            this.shareMenu = null;
        }
    }

    /**
     * Get share URLs from backend
     */
    async getShareUrls() {
        try {
            const response = await fetch(`/peticoes/${this.petitionUuid}/compartilhar/`);
            if (!response.ok) {
                throw new Error('Failed to fetch share URLs');
            }
            return await response.json();
        } catch (error) {
            console.error('Error fetching share URLs:', error);
            return null;
        }
    }

    /**
     * Track share (without showing menu)
     */
    async trackShare() {
        try {
            await fetch(`/peticoes/${this.petitionUuid}/compartilhar/`);
        } catch (error) {
            console.error('Error tracking share:', error);
        }
    }

    /**
     * Show notification message
     */
    showNotification(message) {
        const notification = document.createElement('div');
        notification.className = 'fixed bottom-4 right-4 bg-green-600 text-white px-6 py-3 rounded-lg shadow-lg z-50';
        notification.style.animation = 'slideUp 0.3s ease-out';
        notification.textContent = message;

        document.body.appendChild(notification);

        setTimeout(() => {
            notification.style.animation = 'fadeOut 0.3s ease-out';
            setTimeout(() => notification.remove(), 300);
        }, 2000);
    }
}

// Add CSS animations
const style = document.createElement('style');
style.textContent = `
    @keyframes fadeIn {
        from {
            opacity: 0;
            transform: translateY(-10px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    @keyframes fadeOut {
        from {
            opacity: 1;
        }
        to {
            opacity: 0;
        }
    }

    @keyframes slideUp {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
`;
document.head.appendChild(style);

// Initialize on page load
if (typeof PETITION_UUID !== 'undefined' && typeof PETITION_TITLE !== 'undefined' && typeof PETITION_URL !== 'undefined') {
    document.addEventListener('DOMContentLoaded', () => {
        const shareHandler = new PetitionShare(PETITION_UUID, PETITION_TITLE, PETITION_URL);
        shareHandler.init();
    });
}
