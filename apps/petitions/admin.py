from django.contrib import admin
from .models import Petition, FlaggedContent


@admin.register(Petition)
class PetitionAdmin(admin.ModelAdmin):
    list_display = ['title', 'creator', 'category', 'status', 'signature_count', 'signature_goal', 'created_at']
    list_filter = ['status', 'is_active', 'category', 'created_at']
    search_fields = ['title', 'description', 'creator__username']
    readonly_fields = ['uuid', 'created_at', 'updated_at', 'published_at', 'signature_count', 'view_count', 'share_count']
    prepopulated_fields = {'slug': ('title',)}
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('uuid', 'creator', 'category', 'title', 'slug', 'description')
        }),
        ('Metas', {
            'fields': ('signature_goal', 'deadline')
        }),
        ('Status', {
            'fields': ('status', 'is_active')
        }),
        ('PDF e Verificação', {
            'fields': ('pdf_url', 'content_hash')
        }),
        ('Estatísticas', {
            'fields': ('signature_count', 'view_count', 'share_count')
        }),
        ('Datas', {
            'fields': ('created_at', 'updated_at', 'published_at')
        }),
        ('Moderação', {
            'fields': ('moderation_notes',)
        }),
    )


@admin.register(FlaggedContent)
class FlaggedContentAdmin(admin.ModelAdmin):
    list_display = ['petition', 'reason', 'status', 'reported_by', 'created_at']
    list_filter = ['status', 'reason', 'created_at']
    search_fields = ['petition__title', 'description', 'reporter_email']
    readonly_fields = ['created_at', 'reviewed_at']
    
    fieldsets = (
        ('Denúncia', {
            'fields': ('petition', 'reported_by', 'reporter_email', 'reason', 'description')
        }),
        ('Análise', {
            'fields': ('status', 'reviewed_by', 'review_notes', 'action_taken')
        }),
        ('Segurança', {
            'fields': ('ip_address_hash',)
        }),
        ('Datas', {
            'fields': ('created_at', 'reviewed_at')
        }),
    )
