from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from apps.petitions.models import Petition


class PetitionSitemap(Sitemap):
    """Sitemap for active petitions"""
    changefreq = "daily"
    priority = 0.9
    
    def items(self):
        return Petition.objects.filter(
            status='active',
            is_public=True
        ).order_by('-created_at')
    
    def lastmod(self, obj):
        return obj.updated_at


class StaticViewSitemap(Sitemap):
    """Sitemap for static pages"""
    priority = 0.5
    changefreq = 'weekly'

    def items(self):
        return ['petitions:home', 'petitions:petition_list']

    def location(self, item):
        return reverse(item)
