"""
URL configuration for Petição Brasil project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.sitemaps.views import sitemap
from apps.core.sitemaps import PetitionSitemap, StaticViewSitemap
from apps.core.pwa_views import (
    manifest_view,
    service_worker_view,
    offline_view,
    browserconfig_view,
    PWAInstallView
)

# Sitemap configuration
sitemaps = {
    'petitions': PetitionSitemap,
    'static': StaticViewSitemap,
}

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('apps.accounts.urls')),
    path('signatures/', include('apps.signatures.urls')),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    path('robots.txt', include('robots.urls')),
    
    # PWA URLs
    path('manifest.json', manifest_view, name='manifest'),
    path('service-worker.js', service_worker_view, name='service-worker'),
    path('offline/', offline_view, name='offline'),
    path('browserconfig.xml', browserconfig_view, name='browserconfig'),
    path('pwa/install/', PWAInstallView.as_view(), name='pwa-install'),
    
    path('', include('apps.petitions.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    
    # Django Debug Toolbar
    if 'debug_toolbar' in settings.INSTALLED_APPS:
        urlpatterns = [
            path('__debug__/', include('debug_toolbar.urls')),
        ] + urlpatterns

# Custom admin site configuration
admin.site.site_header = "Petição Brasil Admin"
admin.site.site_title = "Petição Brasil"
admin.site.index_title = "Platform Administration"
