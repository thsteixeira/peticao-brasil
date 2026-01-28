"""
URL configuration for Petição Brasil project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.sitemaps.views import sitemap
from apps.core.sitemaps import PetitionSitemap, StaticViewSitemap

# Sitemap configuration
sitemaps = {
    'petitions': PetitionSitemap,
    'static': StaticViewSitemap,
}

urlpatterns = [
    path('admin/', admin.site.urls),
    path('contas/', include('apps.accounts.urls')),
    path('assinaturas/', include('apps.signatures.urls')),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    path('robots.txt', include('robots.urls')),
    
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
