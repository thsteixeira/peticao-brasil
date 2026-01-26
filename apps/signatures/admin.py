from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from django.db.models import Q
from .models import Signature
from apps.core.models import ModerationLog


def get_client_ip(request):
    """Extract client IP from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


class PendingReviewFilter(admin.SimpleListFilter):
    """Custom filter for signatures pending manual review"""
    title = 'Status de Revisão'
    parameter_name = 'review_status'
    
    def lookups(self, request, model_admin):
        return (
            ('pending_review', 'Pendente de Revisão Manual'),
            ('auto_verified', 'Verificado Automaticamente'),
            ('manually_verified', 'Verificado Manualmente'),
            ('rejected', 'Rejeitado'),
        )
    
    def queryset(self, request, queryset):
        if self.value() == 'pending_review':
            return queryset.filter(verification_status='pending')
        if self.value() == 'auto_verified':
            return queryset.filter(verification_status='verified', verified_at__isnull=False)
        if self.value() == 'manually_verified':
            return queryset.filter(verification_status='verified', verification_notes__icontains='manual')
        if self.value() == 'rejected':
            return queryset.filter(verification_status='rejected')


@admin.register(Signature)
class SignatureAdmin(admin.ModelAdmin):
    list_display = [
        'full_name',
        'petition_link',
        'status_badge',
        'city',
        'state',
        'created_at',
        'verified_at',
        'custody_certificate_link'
    ]
    list_filter = [
        PendingReviewFilter,
        'verification_status',
        'state',
        'verified_cpf_from_certificate',
        'created_at'
    ]
    search_fields = ['full_name', 'email', 'petition__title', 'cpf_hash', 'city', 'uuid']
    readonly_fields = [
        'uuid',
        'cpf_hash',
        'ip_address_hash',
        'created_at',
        'signed_at',
        'verified_at',
        'processing_started_at',
        'processing_completed_at',
        'certificate_generated_at',
        'certificate_info',
        'verification_hash',
        'verification_evidence_display',
        'chain_of_custody_display',
        'custody_certificate_preview'
    ]
    date_hierarchy = 'created_at'
    list_per_page = 50
    
    fieldsets = (
        ('Identificação', {
            'fields': ('uuid', 'petition')
        }),
        ('Dados do Signatário', {
            'fields': ('full_name', 'cpf_hash', 'email', 'city', 'state')
        }),
        ('PDF Assinado', {
            'fields': ('signed_pdf_url', 'signed_pdf_size')
        }),
        ('Verificação', {
            'fields': (
                'verification_status',
                'verification_notes',
                'rejection_reason',
                'verified_cpf_from_certificate',
            )
        }),
        ('Certificado Digital ICP-Brasil', {
            'fields': (
                'certificate_subject',
                'certificate_issuer',
                'certificate_serial',
                'certificate_info'
            )
        }),
        ('Cadeia de Custódia', {
            'fields': (
                'custody_certificate_preview',
                'verification_hash',
                'verification_evidence_display',
                'chain_of_custody_display'
            ),
            'classes': ('collapse',)
        }),
        ('Privacidade', {
            'fields': ('display_name_publicly', 'receive_updates')
        }),
        ('Segurança', {
            'fields': ('ip_address_hash', 'user_agent')
        }),
        ('Timestamps', {
            'fields': (
                'created_at',
                'signed_at',
                'processing_started_at',
                'processing_completed_at',
                'verified_at',
                'certificate_generated_at'
            )
        }),
    )
    
    actions = ['approve_signatures', 'reject_signatures_action', 'mark_for_review', 'regenerate_custody_certificates']
    
    def petition_link(self, obj):
        """Display petition title as clickable link"""
        from django.urls import reverse
        from django.utils.html import escape
        url = reverse('admin:petitions_petition_change', args=[obj.petition.id])
        return format_html('<a href="{}">{}</a>', url, escape(obj.petition.title[:50]))
    petition_link.short_description = 'Petição'
    
    def status_badge(self, obj):
        """Display verification status with color badge"""
        colors = {
            'pending': '#ffc107',  # Yellow
            'verified': '#28a745',  # Green
            'rejected': '#dc3545',  # Red
        }
        color = colors.get(obj.verification_status, '#6c757d')
        status_text = obj.get_verification_status_display()
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">{}</span>',
            color, status_text
        )
    status_badge.short_description = 'Status'
    
    def approve_signatures(self, request, queryset):
        """Bulk approve signatures with moderation log"""
        count = 0
        for signature in queryset.filter(verification_status='pending'):
            signature.verification_notes = f"Aprovado manualmente por {request.user.username}"
            signature.save()
            
            # Use approve() method to ensure count is incremented
            signature.approve()
            
            # Log the action
            ModerationLog.log_action(
                moderator=request.user,
                action_type='signature_approve',
                content_type='signature',
                object_id=signature.uuid,
                reason='Aprovação manual via admin',
                ip_address=get_client_ip(request)
            )
            count += 1
        
        if count == 1:
            ModerationLog.log_action(
                moderator=request.user,
                action_type='signature_bulk_approve',
                content_type='signature',
                object_id='bulk',
                notes=f"{count} assinatura aprovada",
                ip_address=get_client_ip(request)
            )
        elif count > 1:
            ModerationLog.log_action(
                moderator=request.user,
                action_type='signature_bulk_approve',
                content_type='signature',
                object_id='bulk',
                notes=f"{count} assinaturas aprovadas",
                ip_address=get_client_ip(request)
            )
        
        self.message_user(request, f"{count} assinatura(s) aprovada(s) com sucesso.")
    approve_signatures.short_description = "✓ Aprovar assinaturas selecionadas"
    
    def reject_signatures_action(self, request, queryset):
        """Bulk reject signatures with moderation log"""
        count = 0
        for signature in queryset.filter(Q(verification_status='pending') | Q(verification_status='verified')):
            signature.verification_status = 'rejected'
            signature.verification_notes = f"Rejeitado manualmente por {request.user.username}"
            signature.save()
            
            # Log the action
            ModerationLog.log_action(
                moderator=request.user,
                action_type='signature_reject',
                content_type='signature',
                object_id=signature.uuid,
                reason='Rejeição manual via admin',
                ip_address=get_client_ip(request)
            )
            count += 1
        
        if count > 0:
            ModerationLog.log_action(
                moderator=request.user,
                action_type='signature_bulk_reject',
                content_type='signature',
                object_id='bulk',
                notes=f"{count} assinaturas rejeitadas",
                ip_address=get_client_ip(request)
            )
        
        self.message_user(request, f"{count} assinatura(s) rejeitada(s).", level='warning')
    reject_signatures_action.short_description = "✗ Rejeitar assinaturas selecionadas"
    
    def mark_for_review(self, request, queryset):
        """Mark signatures for manual review"""
        count = queryset.filter(verification_status='verified').update(
            verification_status='pending',
            verification_notes='Marcado para revisão manual'
        )
        self.message_user(request, f"{count} assinatura(s) marcada(s) para revisão.")
    mark_for_review.short_description = "⚠ Marcar para revisão manual"
    
    def custody_certificate_link(self, obj):
        """Display link to custody certificate in list view."""
        if obj.custody_certificate_url and obj.verification_status == Signature.STATUS_APPROVED:
            return format_html(
                '<a href="{}" target="_blank">📄 Ver</a>',
                obj.custody_certificate_url
            )
        return '-'
    custody_certificate_link.short_description = 'Certificado'
    
    def custody_certificate_preview(self, obj):
        """Display custody certificate with download link in detail view."""
        if obj.custody_certificate_url:
            return format_html(
                '<a href="{}" target="_blank" class="button">📄 Baixar Certificado de Custódia</a><br>'
                '<small>Hash de Verificação: <code>{}</code></small><br>'
                '<small>Gerado em: {}</small>',
                obj.custody_certificate_url,
                obj.verification_hash or 'N/A',
                obj.certificate_generated_at.strftime('%d/%m/%Y %H:%M:%S') if obj.certificate_generated_at else 'N/A'
            )
        return format_html('<em>Certificado não gerado</em>')
    custody_certificate_preview.short_description = 'Certificado de Custódia'
    
    def verification_evidence_display(self, obj):
        """Display verification evidence as formatted JSON."""
        if obj.verification_evidence:
            import json
            evidence_pretty = json.dumps(obj.verification_evidence, indent=2, ensure_ascii=False)
            return format_html('<pre style="font-size: 11px; max-height: 400px; overflow: auto;">{}</pre>', evidence_pretty)
        return '-'
    verification_evidence_display.short_description = 'Evidências de Verificação'
    
    def chain_of_custody_display(self, obj):
        """Display chain of custody timeline."""
        if obj.chain_of_custody:
            import json
            chain_pretty = json.dumps(obj.chain_of_custody, indent=2, ensure_ascii=False)
            return format_html('<pre style="font-size: 11px; max-height: 400px; overflow: auto;">{}</pre>', chain_pretty)
        return '-'
    chain_of_custody_display.short_description = 'Cadeia de Custódia'
    
    def regenerate_custody_certificates(self, request, queryset):
        """Admin action to regenerate custody certificates."""
        from apps.signatures.custody_service import generate_custody_certificate
        
        count = 0
        errors = 0
        for signature in queryset.filter(verification_status=Signature.STATUS_APPROVED):
            try:
                generate_custody_certificate(signature)
                count += 1
            except Exception as e:
                errors += 1
                self.message_user(
                    request,
                    f'Erro ao regenerar certificado para {signature.uuid}: {str(e)}',
                    level='error'
                )
        
        if count > 0:
            self.message_user(
                request,
                f'{count} certificado(s) regenerado(s) com sucesso.',
                level='success'
            )
        if errors > 0:
            self.message_user(
                request,
                f'{errors} erro(s) ao regenerar certificados.',
                level='warning'
            )
    
    regenerate_custody_certificates.short_description = '🔄 Regenerar certificados de custódia'
    
    def get_queryset(self, request):
        """Optimize queries with select_related"""
        qs = super().get_queryset(request)
        return qs.select_related('petition')
    
    class Media:
        css = {
            'all': ('admin/css/custom_admin.css',)
        }

