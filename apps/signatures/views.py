"""
Views for signature submission and management.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView, ListView
from django.urls import reverse
from django.utils import timezone
from django.db import transaction
from django.utils.decorators import method_decorator

from apps.petitions.models import Petition
from apps.core.rate_limiting import rate_limit
from apps.core.google_tracking import GoogleAnalyticsEventMixin
from .models import Signature
from .forms import SignatureSubmissionForm


@method_decorator(rate_limit(max_requests=10, window=3600), name='post')  # 10 uploads per hour
class SignatureSubmitView(GoogleAnalyticsEventMixin, CreateView):
    """
    View for submitting a signed PDF with rate limiting.
    """
    model = Signature
    form_class = SignatureSubmissionForm
    template_name = 'signatures/signature_submit.html'
    ga_event_name = 'signature_submitted'
    
    def dispatch(self, request, *args, **kwargs):
        """Get petition and validate it can receive signatures."""
        self.petition = get_object_or_404(Petition, uuid=kwargs.get('uuid'))
        
        # Check if petition is active
        if self.petition.status != 'active':
            messages.error(request, 'Esta petição não está mais aceitando assinaturas.')
            return redirect('petitions:detail', uuid=self.petition.uuid)
        
        # Check if deadline has passed
        if self.petition.deadline and self.petition.deadline < timezone.now().date():
            messages.error(request, 'O prazo para assinar esta petição já expirou.')
            return redirect('petitions:detail', uuid=self.petition.uuid)
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_ga_event_params(self):
        """Track signature submission with petition details."""
        return {
            'petition_id': str(self.petition.uuid),
            'petition_category': self.petition.category.name if self.petition.category else 'uncategorized',
            'petition_signature_count': self.petition.signature_count + 1  # Include the new signature
        }
    
    def get_context_data(self, **kwargs):
        """Add petition to context."""
        context = super().get_context_data(**kwargs)
        context['petition'] = self.petition
        return context
    
    def get_form_kwargs(self):
        """Pass petition and request to form."""
        kwargs = super().get_form_kwargs()
        kwargs['petition'] = self.petition
        kwargs['request'] = self.request
        return kwargs
    
    def form_valid(self, form):
        """Process valid signature submission."""
        try:
            with transaction.atomic():
                # Set petition
                form.instance.petition = self.petition
                
                # Hash CPF
                cpf = form.cleaned_data.get('cpf')
                if not cpf:
                    raise ValueError('CPF cannot be None in form_valid')
                
                form.instance.cpf_hash = Signature.hash_cpf(cpf)
                
                # Store file hash
                if 'file_hash' in form.cleaned_data:
                    form.instance.file_hash = form.cleaned_data['file_hash']
                
                # Get client IP for tracking
                x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
                if x_forwarded_for:
                    ip = x_forwarded_for.split(',')[0]
                else:
                    ip = self.request.META.get('REMOTE_ADDR')
                
                # Hash IP address for LGPD compliance
                form.instance.ip_address_hash = Signature.hash_ip(ip)
                
                # Set initial status as pending
                form.instance.verification_status = 'pending'
                
                # Save signature
                signature = form.save()
                
                messages.success(
                    self.request,
                    'Assinatura enviada com sucesso! Aguarde a verificação do certificado digital.'
                )
                
                # Trigger async verification task (with fallback for development)
                try:
                    from .tasks import verify_signature
                    verify_signature.delay(signature.id)
                except Exception as e:
                    # Fallback to synchronous verification if Celery/Redis is not available
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning(f"Celery not available, verifying signature synchronously: {e}")
                    
                    try:
                        from .verification_service import PDFSignatureVerifier
                        
                        sig = Signature.objects.get(id=signature.id)
                        verifier = PDFSignatureVerifier()
                        result = verifier.verify_pdf_signature(sig.signed_pdf, sig.petition)
                        
                        if result['verified']:
                            sig.verified = True
                            sig.certificate_subject = result['certificate_info'].get('subject', '')[:500]
                            sig.certificate_issuer = result['certificate_info'].get('issuer', '')[:500]
                            sig.certificate_serial = result['certificate_info'].get('serial_number', '')[:100]
                            sig.save()
                            # Approve signature (this increments the petition count)
                            sig.approve()
                            messages.info(self.request, 'Certificado digital verificado com sucesso!')
                        else:
                            sig.verification_status = Signature.STATUS_REJECTED
                            sig.rejection_reason = result.get('error', 'Falha na verificação')
                            sig.save()
                            messages.warning(self.request, f'Assinatura rejeitada: {sig.rejection_reason}')
                    except Exception as verify_error:
                        logger.error(f"Failed to verify signature: {verify_error}")
                        messages.warning(self.request, 'A verificação será processada posteriormente.')
                
                return redirect('petitions:detail', uuid=self.petition.uuid, slug=self.petition.slug)
        
        except Exception as e:
            messages.error(
                self.request,
                f'Erro ao processar assinatura: {str(e)}'
            )
            return self.form_invalid(form)
    
    def get_success_url(self):
        """Redirect to petition detail after submission."""
        return reverse('petitions:detail', kwargs={'uuid': self.petition.uuid})


class MySignaturesView(LoginRequiredMixin, ListView):
    """
    View to list signatures submitted by the current user.
    Requires authentication.
    """
    model = Signature
    template_name = 'signatures/my_signatures.html'
    context_object_name = 'signatures'
    paginate_by = 20
    
    def get_queryset(self):
        """Get signatures filtered by user's email."""
        queryset = Signature.objects.select_related('petition', 'petition__category')
        
        # Filter by user's email
        user_email = self.request.user.email
        if user_email:
            queryset = queryset.filter(email=user_email)
        
        return queryset.order_by('-created_at')


class PetitionSignaturesView(ListView):
    """
    View to list all signatures for a specific petition (for petition creator/admin).
    """
    model = Signature
    template_name = 'signatures/petition_signatures.html'
    context_object_name = 'signatures'
    paginate_by = 50
    
    def dispatch(self, request, *args, **kwargs):
        """Get petition and check permissions."""
        self.petition = get_object_or_404(Petition, uuid=kwargs.get('uuid'))
        
        # Only petition creator or staff can view signatures
        if not (request.user.is_authenticated and 
                (request.user == self.petition.creator or request.user.is_staff)):
            messages.error(request, 'Você não tem permissão para visualizar estas assinaturas.')
            return redirect('petitions:detail', uuid=self.petition.uuid, slug=self.petition.slug)
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        """Get signatures for this petition."""
        return Signature.objects.filter(
            petition=self.petition
        ).order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        """Add petition and statistics to context."""
        context = super().get_context_data(**kwargs)
        context['petition'] = self.petition
        context['is_staff'] = self.request.user.is_staff
        
        # Add statistics
        signatures = self.get_queryset()
        context['total_signatures'] = signatures.count()
        context['approved_signatures'] = signatures.filter(verification_status='approved').count()
        context['pending_signatures'] = signatures.filter(verification_status='pending').count()
        context['rejected_signatures'] = signatures.filter(verification_status='rejected').count()
        
        # Signatures by state (only for staff)
        if self.request.user.is_staff:
            context['signatures_by_state'] = signatures.values(
                'state'
            ).annotate(
                count=models.Count('id')
            ).order_by('-count')[:10]
        
        return context


# Import Count for statistics
from django.db import models
from django.views.generic import View
from django.http import HttpResponse, JsonResponse
import hashlib
import json


class DownloadCustodyCertificateView(GoogleAnalyticsEventMixin, View):
    """Allow users to download their custody certificate."""
    ga_event_name = 'file_download'
    
    def get_ga_event_params(self):
        """Track custody certificate downloads."""
        return {
            'file_type': 'pdf',
            'content_type': 'custody_certificate'
        }
    
    def get(self, request, uuid):
        """Serve the custody certificate PDF."""
        signature = get_object_or_404(
            Signature.objects.select_related('petition'),
            uuid=uuid,
            verification_status=Signature.STATUS_APPROVED
        )
        
        if not signature.custody_certificate_url:
            return HttpResponse(
                'Certificado de custódia não disponível. '
                'Entre em contato com o suporte se você acredita que isto é um erro.',
                status=404
            )
        
        # Redirect to S3 URL
        return redirect(signature.custody_certificate_url)


class VerifyCustodyCertificateView(View):
    """View to verify certificate authenticity - supports both HTML and JSON."""
    
    def get(self, request, uuid):
        """Return certificate verification data as HTML or JSON."""
        signature = get_object_or_404(
            Signature.objects.select_related('petition'),
            uuid=uuid,
            verification_status=Signature.STATUS_APPROVED
        )
        
        # Recalculate hash to verify integrity
        integrity_verified = False
        if signature.verification_evidence and signature.verification_hash:
            evidence_json = json.dumps(
                signature.verification_evidence,
                sort_keys=True,
                ensure_ascii=False
            )
            calculated_hash = hashlib.sha256(
                evidence_json.encode('utf-8')
            ).hexdigest()
            
            integrity_verified = (calculated_hash == signature.verification_hash)
        
        # Return JSON if requested via Accept header or query parameter
        if request.GET.get('format') == 'json' or request.META.get('HTTP_ACCEPT', '').startswith('application/json'):
            return JsonResponse({
                'signature_uuid': str(signature.uuid),
                'petition_title': signature.petition.title,
                'petition_uuid': str(signature.petition.uuid),
                'signer_name': signature.full_name,
                'signed_at': signature.signed_at.isoformat() if signature.signed_at else None,
                'verified_at': signature.verified_at.isoformat() if signature.verified_at else None,
                'verification_hash': signature.verification_hash,
                'integrity_verified': integrity_verified,
                'certificate_url': signature.custody_certificate_url,
                'certificate_generated_at': signature.certificate_generated_at.isoformat() if signature.certificate_generated_at else None,
                'status': 'valid' if integrity_verified else 'integrity_check_failed',
            })
        
        # Return HTML page for browser/QR code access
        context = {
            'signature': signature,
            'integrity_verified': integrity_verified,
        }
        return render(request, 'signatures/verify_certificate.html', context)
