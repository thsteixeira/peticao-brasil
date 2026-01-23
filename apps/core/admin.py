from django.contrib import admin
from django.shortcuts import render
from django.utils import timezone
from datetime import timedelta
from .models import Category, ModerationLog


class CustomAdminSite(admin.AdminSite):
    """
    Custom admin site with moderation dashboard.
    """
    site_header = 'Petição Brasil - Painel de Administração'
    site_title = 'Petição Brasil Admin'
    index_title = 'Dashboard de Moderação'
    
    def index(self, request, extra_context=None):
        """
        Custom admin index with statistics.
        """
        from apps.signatures.models import Signature
        from apps.petitions.models import Petition, FlaggedContent
        
        # Calculate statistics
        pending_signatures = Signature.objects.filter(verification_status='pending').count()
        pending_petitions = Petition.objects.filter(status='draft', is_active=True).count()
        
        today = timezone.now().date()
        signatures_today = Signature.objects.filter(created_at__date=today).count()
        
        active_petitions = Petition.objects.filter(
            status='published',
            is_active=True
        ).count()
        
        # Recent moderation logs
        recent_logs = ModerationLog.objects.select_related('moderator')[:10]
        
        extra_context = extra_context or {}
        extra_context.update({
            'pending_signatures': pending_signatures,
            'pending_petitions': pending_petitions,
            'signatures_today': signatures_today,
            'active_petitions': active_petitions,
            'recent_logs': recent_logs,
        })
        
        return super().index(request, extra_context=extra_context)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'color', 'order', 'active', 'petition_count']
    list_filter = ['active']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['order', 'name']


@admin.register(ModerationLog)
class ModerationLogAdmin(admin.ModelAdmin):
    list_display = ['action_type', 'moderator', 'content_type', 'created_at']
    list_filter = ['action_type', 'content_type', 'created_at']
    search_fields = ['moderator__username', 'reason', 'notes', 'object_id']
    readonly_fields = ['id', 'moderator', 'action_type', 'content_type', 'object_id', 'reason', 'notes', 'ip_address', 'created_at']
    date_hierarchy = 'created_at'
    list_per_page = 100
    
    def has_add_permission(self, request):
        """Prevent manual creation of logs"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Only superusers can delete logs"""
        return request.user.is_superuser

