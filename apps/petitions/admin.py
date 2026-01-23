from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from django.db.models import Count, Q
from django.urls import reverse
from .models import Petition, FlaggedContent
from apps.core.models import ModerationLog


def get_client_ip(request):
    """Extract client IP from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


class ModerationFilter(admin.SimpleListFilter):
    """Custom filter for petition moderation status"""
    title = 'Status de Moderação'
    parameter_name = 'moderation'
    
    def lookups(self, request, model_admin):
        return (
            ('needs_approval', 'Aguardando Aprovação'),
            ('published', 'Publicada'),
            ('rejected', 'Rejeitada'),
            ('has_flags', 'Com Denúncias'),
        )
    
    def queryset(self, request, queryset):
        if self.value() == 'needs_approval':
            return queryset.filter(status='draft', is_active=True)
        if self.value() == 'published':
            return queryset.filter(status='published')
        if self.value() == 'rejected':
            return queryset.filter(status='rejected')
        if self.value() == 'has_flags':
            return queryset.filter(flags__status='pending').distinct()


class SignatureCountFilter(admin.SimpleListFilter):
    """Filter petitions by signature count ranges"""
    title = 'Número de Assinaturas'
    parameter_name = 'signature_range'
    
    def lookups(self, request, model_admin):
        return (
            ('none', 'Sem assinaturas'),
            ('low', '1-99'),
            ('medium', '100-999'),
            ('high', '1000-9999'),
            ('viral', '10000+'),
        )
    
    def queryset(self, request, queryset):
        if self.value() == 'none':
            return queryset.filter(signature_count=0)
        if self.value() == 'low':
            return queryset.filter(signature_count__gte=1, signature_count__lt=100)
        if self.value() == 'medium':
            return queryset.filter(signature_count__gte=100, signature_count__lt=1000)
        if self.value() == 'high':
            return queryset.filter(signature_count__gte=1000, signature_count__lt=10000)
        if self.value() == 'viral':
            return queryset.filter(signature_count__gte=10000)


@admin.register(Petition)
class PetitionAdmin(admin.ModelAdmin):
    list_display = ['title_link', 'creator', 'category', 'status_badge', 'progress_bar', 'signature_goal', 'created_at']
    list_filter = [ModerationFilter, SignatureCountFilter, 'status', 'is_active', 'category', 'created_at']
    search_fields = ['title', 'description', 'creator__username', 'creator__email']
    readonly_fields = ['uuid', 'created_at', 'updated_at', 'published_at', 'signature_count', 'view_count', 'share_count']
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'created_at'
    list_per_page = 25
    
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
            'fields': ('moderation_notes',),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['approve_petitions', 'reject_petitions', 'archive_petitions', 'publish_petitions']
    
    def title_link(self, obj):
        """Display title as clickable link"""
        from django.utils.html import escape
        # Allow links for active, completed, and expired petitions
        viewable_statuses = ['active', 'completed', 'expired', 'closed']
        url = obj.get_absolute_url() if obj.status in viewable_statuses else '#'
        return format_html('<a href="{}" target="_blank">{}</a>', 
                          url,
                          escape(obj.title[:60]))
    title_link.short_description = 'Título'
    
    def status_badge(self, obj):
        """Display status with color badge"""
        colors = {
            'draft': '#6c757d',     # Gray
            'published': '#28a745',  # Green
            'closed': '#17a2b8',     # Blue
            'rejected': '#dc3545',   # Red
        }
        color = colors.get(obj.status, '#6c757d')
        status_text = obj.get_status_display()
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold; font-size: 11px;">{}</span>',
            color, status_text
        )
    status_badge.short_description = 'Status'
    
    def progress_bar(self, obj):
        """Visual progress bar for signatures"""
        if obj.signature_goal > 0:
            percentage = min(100, int((obj.signature_count / obj.signature_goal) * 100))
            color = '#28a745' if percentage >= 100 else '#007bff' if percentage >= 50 else '#ffc107'
            return format_html(
                '<div style="width: 100px; background-color: #e9ecef; border-radius: 3px; overflow: hidden;">'
                '<div style="width: {}%; background-color: {}; color: white; text-align: center; font-size: 10px; font-weight: bold; padding: 2px;">{}/{}</div>'
                '</div>',
                percentage, color, obj.signature_count, obj.signature_goal
            )
        return format_html('<span>{} assinaturas</span>', obj.signature_count)
    progress_bar.short_description = 'Progresso'
    
    def approve_petitions(self, request, queryset):
        """Approve and publish petitions"""
        count = 0
        for petition in queryset.filter(status__in=['draft', 'rejected']):
            petition.status = 'published'
            petition.published_at = timezone.now()
            petition.is_active = True
            petition.moderation_notes = f"Aprovado por {request.user.username} em {timezone.now().strftime('%d/%m/%Y %H:%M')}"
            petition.save()
            
            # Log the action
            ModerationLog.log_action(
                moderator=request.user,
                action_type='petition_approve',
                content_type='petition',
                object_id=petition.uuid,
                reason='Aprovação e publicação via admin',
                ip_address=get_client_ip(request)
            )
            count += 1
        
        self.message_user(request, f"{count} petição(ões) aprovada(s) e publicada(s).")
    approve_petitions.short_description = "✓ Aprovar e publicar petições"
    
    def reject_petitions(self, request, queryset):
        """Reject petitions"""
        count = 0
        for petition in queryset.exclude(status='rejected'):
            petition.status = 'rejected'
            petition.is_active = False
            petition.moderation_notes = f"Rejeitado por {request.user.username} em {timezone.now().strftime('%d/%m/%Y %H:%M')}"
            petition.save()
            
            # Log the action
            ModerationLog.log_action(
                moderator=request.user,
                action_type='petition_reject',
                content_type='petition',
                object_id=petition.uuid,
                reason='Rejeição via admin',
                ip_address=get_client_ip(request)
            )
            count += 1
        
        self.message_user(request, f"{count} petição(ões) rejeitada(s).", level='warning')
    reject_petitions.short_description = "✗ Rejeitar petições"
    
    def archive_petitions(self, request, queryset):
        """Archive petitions (close without rejection)"""
        count = 0
        for petition in queryset.exclude(status='closed'):
            petition.status = 'closed'
            petition.is_active = False
            petition.moderation_notes = f"Arquivado por {request.user.username} em {timezone.now().strftime('%d/%m/%Y %H:%M')}"
            petition.save()
            
            # Log the action
            ModerationLog.log_action(
                moderator=request.user,
                action_type='petition_archive',
                content_type='petition',
                object_id=petition.uuid,
                reason='Arquivamento via admin',
                ip_address=get_client_ip(request)
            )
            count += 1
        
        self.message_user(request, f"{count} petição(ões) arquivada(s).")
    archive_petitions.short_description = "📁 Arquivar petições"
    
    def publish_petitions(self, request, queryset):
        """Publish draft petitions"""
        count = queryset.filter(status='draft').update(
            status='published',
            published_at=timezone.now(),
            is_active=True
        )
        self.message_user(request, f"{count} petição(ões) publicada(s).")
    publish_petitions.short_description = "📢 Publicar petições (rascunho)"
    
    def get_queryset(self, request):
        """Optimize queries"""
        qs = super().get_queryset(request)
        return qs.select_related('creator', 'category').annotate(
            flag_count=Count('flags', filter=Q(flags__status='pending'))
        )


@admin.register(FlaggedContent)
class FlaggedContentAdmin(admin.ModelAdmin):
    list_display = ['petition_link', 'reason', 'status_badge', 'reported_by', 'created_at']
    list_filter = ['status', 'reason', 'created_at']
    search_fields = ['petition__title', 'description', 'reporter_email']
    readonly_fields = ['created_at', 'reviewed_at', 'ip_address_hash']
    date_hierarchy = 'created_at'
    list_per_page = 50
    
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
    
    actions = ['mark_as_resolved', 'mark_as_dismissed']
    
    def petition_link(self, obj):
        """Display petition title as link to petition admin"""
        url = reverse('admin:petitions_petition_change', args=[obj.petition.id])
        return format_html('<a href="{}">{}</a>', url, obj.petition.title[:60])
    petition_link.short_description = 'Petição'
    
    def status_badge(self, obj):
        """Display status with color badge"""
        colors = {
            'pending': '#ffc107',
            'reviewed': '#28a745',
            'dismissed': '#6c757d',
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px; font-size: 11px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def mark_as_resolved(self, request, queryset):
        """Mark flags as reviewed and resolved"""
        count = queryset.filter(status='pending').update(
            status='reviewed',
            reviewed_by=request.user,
            reviewed_at=timezone.now()
        )
        self.message_user(request, f"{count} denúncia(s) marcada(s) como resolvida(s).")
    mark_as_resolved.short_description = "✓ Marcar como resolvido"
    
    def mark_as_dismissed(self, request, queryset):
        """Dismiss flags as invalid"""
        count = queryset.filter(status='pending').update(
            status='dismissed',
            reviewed_by=request.user,
            reviewed_at=timezone.now()
        )
        self.message_user(request, f"{count} denúncia(s) descartada(s).")
    mark_as_dismissed.short_description = "✗ Descartar denúncia"
    
    def get_queryset(self, request):
        """Optimize queries"""
        qs = super().get_queryset(request)
        return qs.select_related('petition', 'reported_by', 'reviewed_by')

