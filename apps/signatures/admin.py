from django.contrib import admin
from .models import Signature


@admin.register(Signature)
class SignatureAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'petition', 'verification_status', 'city', 'state', 'created_at', 'verified_at']
    list_filter = ['verification_status', 'state', 'verified_cpf_from_certificate', 'created_at']
    search_fields = ['full_name', 'email', 'petition__title', 'cpf_hash']
    readonly_fields = ['uuid', 'cpf_hash', 'ip_address_hash', 'created_at', 'signed_at', 'verified_at', 'certificate_info']
    
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
            'fields': ('verification_status', 'verification_notes', 'verified_cpf_from_certificate', 'certificate_info')
        }),
        ('Privacidade', {
            'fields': ('display_name_publicly', 'receive_updates')
        }),
        ('Segurança', {
            'fields': ('ip_address_hash', 'user_agent')
        }),
        ('Datas', {
            'fields': ('created_at', 'signed_at', 'verified_at')
        }),
    )
    
    actions = ['approve_signatures', 'reject_signatures']
    
    def approve_signatures(self, request, queryset):
        for signature in queryset:
            signature.approve()
        self.message_user(request, f"{queryset.count()} assinaturas aprovadas com sucesso.")
    approve_signatures.short_description = "Aprovar assinaturas selecionadas"
    
    def reject_signatures(self, request, queryset):
        for signature in queryset:
            signature.reject("Rejeitado pelo administrador")
        self.message_user(request, f"{queryset.count()} assinaturas rejeitadas.")
    reject_signatures.short_description = "Rejeitar assinaturas selecionadas"
