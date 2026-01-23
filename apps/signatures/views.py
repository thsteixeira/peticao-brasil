"""
Views for signature submission and management.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.generic import CreateView, ListView
from django.urls import reverse
from django.utils import timezone
from django.db import transaction
from django.utils.decorators import method_decorator

from apps.petitions.models import Petition
from apps.core.rate_limiting import rate_limit
from .models import Signature
from .forms import SignatureSubmissionForm


@method_decorator(rate_limit(max_requests=10, window=3600), name='post')  # 10 uploads per hour
class SignatureSubmitView(CreateView):
    """
    View for submitting a signed PDF with rate limiting.
    """
    model = Signature
    form_class = SignatureSubmissionForm
    template_name = 'signatures/signature_submit.html'
    
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
                cpf = form.cleaned_data['cpf']
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
                            sig.verification_status = Signature.STATUS_APPROVED
                            sig.verified = True
                            sig.verified_at = timezone.now()
                            sig.certificate_subject = result['certificate_info'].get('subject', '')[:500]
                            sig.certificate_issuer = result['certificate_info'].get('issuer', '')[:500]
                            sig.certificate_serial = result['certificate_info'].get('serial_number', '')[:100]
                            sig.save()
                            sig.petition.increment_signature_count()
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


class MySignaturesView(ListView):
    """
    View to list signatures submitted by the current user.
    """
    model = Signature
    template_name = 'signatures/my_signatures.html'
    context_object_name = 'signatures'
    paginate_by = 20
    
    def get_queryset(self):
        """Get signatures filtered by user's email if provided."""
        queryset = Signature.objects.select_related('petition', 'petition__category')
        
        # Filter by email if user is logged in
        if self.request.user.is_authenticated:
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
            return redirect('petitions:detail', uuid=self.petition.uuid)
        
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
        
        # Add statistics
        signatures = self.get_queryset()
        context['total_signatures'] = signatures.count()
        context['approved_signatures'] = signatures.filter(status='approved').count()
        context['pending_signatures'] = signatures.filter(status='pending').count()
        context['rejected_signatures'] = signatures.filter(status='rejected').count()
        
        # Signatures by state
        context['signatures_by_state'] = signatures.values(
            'state'
        ).annotate(
            count=models.Count('id')
        ).order_by('-count')[:10]
        
        return context


# Import Count for statistics
from django.db import models
