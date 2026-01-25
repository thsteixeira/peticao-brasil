"""
PWA (Progressive Web App) views and utilities.
"""
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_GET
from django.views.decorators.cache import cache_page
from django.conf import settings
from django.shortcuts import render
from django.views import View
import json


@require_GET
@cache_page(60 * 60 * 24)  # Cache for 24 hours
def manifest_view(request):
    """
    Serve the PWA manifest.json dynamically.
    """
    manifest = {
        "name": getattr(settings, 'SITE_NAME', 'Petição Brasil') + " - Democracia Direta",
        "short_name": getattr(settings, 'SITE_NAME', 'Petição Brasil'),
        "description": "Plataforma democrática para petições públicas com assinatura digital Gov.br",
        "start_url": "/",
        "scope": "/",
        "display": "standalone",
        "background_color": "#ffffff",
        "theme_color": "#2563eb",
        "orientation": "portrait-primary",
        "icons": [
            {
                "src": request.build_absolute_uri(settings.STATIC_URL + "images/favicon_io/android-chrome-192x192.png"),
                "sizes": "192x192",
                "type": "image/png",
                "purpose": "any maskable"
            },
            {
                "src": request.build_absolute_uri(settings.STATIC_URL + "images/favicon_io/android-chrome-512x512.png"),
                "sizes": "512x512",
                "type": "image/png",
                "purpose": "any maskable"
            }
        ],
        "categories": ["government", "social", "utilities"],
        "lang": "pt-BR",
        "dir": "ltr",
        "shortcuts": [
            {
                "name": "Ver Petições",
                "short_name": "Petições",
                "description": "Ver todas as petições ativas",
                "url": "/peticoes/",
                "icons": [
                    {
                        "src": request.build_absolute_uri(settings.STATIC_URL + "images/favicon_io/android-chrome-192x192.png"),
                        "sizes": "192x192"
                    }
                ]
            },
            {
                "name": "Criar Petição",
                "short_name": "Criar",
                "description": "Criar uma nova petição",
                "url": "/criar/",
                "icons": [
                    {
                        "src": request.build_absolute_uri(settings.STATIC_URL + "images/favicon_io/android-chrome-192x192.png"),
                        "sizes": "192x192"
                    }
                ]
            },
            {
                "name": "Minhas Assinaturas",
                "short_name": "Assinaturas",
                "description": "Ver minhas assinaturas",
                "url": "/signatures/minhas-assinaturas/",
                "icons": [
                    {
                        "src": request.build_absolute_uri(settings.STATIC_URL + "images/favicon_io/android-chrome-192x192.png"),
                        "sizes": "192x192"
                    }
                ]
            }
        ],
        "prefer_related_applications": False
    }
    
    return JsonResponse(manifest, content_type='application/manifest+json')


@require_GET
def service_worker_view(request):
    """
    Serve the service worker JavaScript file.
    IMPORTANT: No caching! Service worker needs to check for updates frequently.
    """
    with open(settings.BASE_DIR / 'static' / 'js' / 'service-worker.js', 'r', encoding='utf-8') as f:
        content = f.read()
    
    response = HttpResponse(content, content_type='application/javascript')
    # Prevent caching of service worker - browsers need to check for updates
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    
    return response


@require_GET
def offline_view(request):
    """
    Offline fallback page.
    """
    return render(request, 'offline.html')


@require_GET
@cache_page(60 * 60 * 24)  # Cache for 24 hours
def browserconfig_view(request):
    """
    Serve browserconfig.xml for Microsoft tiles.
    """
    xml_content = f"""<?xml version="1.0" encoding="utf-8"?>
<browserconfig>
    <msapplication>
        <tile>
            <square150x150logo src="{request.build_absolute_uri(settings.STATIC_URL)}images/icons/icon-144x144.png"/>
            <TileColor>#2563eb</TileColor>
        </tile>
    </msapplication>
</browserconfig>"""
    
    return HttpResponse(xml_content, content_type='application/xml')


class PWAInstallView(View):
    """
    View to track PWA installations (for analytics).
    """
    def post(self, request):
        # Log PWA installation
        # You can add analytics tracking here
        return JsonResponse({'status': 'success'})
