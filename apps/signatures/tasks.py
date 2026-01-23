"""
Celery tasks for signature verification.
"""
from celery import shared_task
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def verify_signature(self, signature_id):
    """
    Async task to verify a signature's digital certificate.
    """
    try:
        from apps.signatures.models import Signature
        from apps.signatures.verification_service import PDFSignatureVerifier
        
        # Get signature
        signature = Signature.objects.get(id=signature_id)
        
        logger.info(f"Verifying signature {signature.uuid}")
        
        # Update status to processing
        signature.verification_status = Signature.STATUS_PROCESSING
        signature.save(update_fields=['verification_status'])
        
        # Initialize verifier
        verifier = PDFSignatureVerifier()
        
        # Verify the signature
        result = verifier.verify_pdf_signature(
            signature.signed_pdf,
            signature.petition
        )
        
        if result['verified']:
            # Signature is valid
            signature.verification_status = Signature.STATUS_APPROVED
            signature.verified = True
            signature.verified_at = timezone.now()
            
            # Store certificate information
            if result['certificate_info']:
                cert_info = result['certificate_info']
                signature.certificate_subject = cert_info.get('subject', '')
                signature.certificate_issuer = cert_info.get('issuer', '')
                signature.certificate_serial = cert_info.get('serial_number', '')
            
            signature.save()
            
            # Increment petition signature count
            signature.petition.increment_signature_count()
            
            logger.info(f"Signature {signature.uuid} verified successfully")
            
            return {
                'success': True,
                'signature_uuid': str(signature.uuid),
                'status': 'approved'
            }
        else:
            # Signature verification failed
            signature.verification_status = Signature.STATUS_REJECTED
            signature.rejection_reason = result.get('error', 'Verificação falhou')
            signature.save()
            
            logger.warning(
                f"Signature {signature.uuid} rejected: {signature.rejection_reason}"
            )
            
            return {
                'success': False,
                'signature_uuid': str(signature.uuid),
                'status': 'rejected',
                'reason': signature.rejection_reason
            }
        
    except ObjectDoesNotExist:
        logger.error(f"Signature with id {signature_id} not found")
        raise
    
    except Exception as exc:
        logger.error(f"Error verifying signature {signature_id}: {str(exc)}")
        
        # Update signature to manual review on error
        try:
            signature = Signature.objects.get(id=signature_id)
            signature.verification_status = Signature.STATUS_MANUAL_REVIEW
            signature.rejection_reason = f"Erro na verificação automática: {str(exc)}"
            signature.save()
        except:
            pass
        
        # Retry the task
        raise self.retry(exc=exc, countdown=60)


@shared_task(name='apps.signatures.tasks.verify_pending_signatures')
def verify_pending_signatures():
    """
    Periodic task to verify all pending signatures.
    Runs every 5 minutes via Celery Beat.
    """
    from apps.signatures.models import Signature
    
    try:
        pending_signatures = Signature.objects.filter(
            verification_status=Signature.STATUS_PENDING
        )[:50]  # Limit to 50 at a time
        
        count = 0
        for signature in pending_signatures:
            try:
                verify_signature.delay(signature.id)
                count += 1
            except Exception as e:
                logger.error(f'Failed to queue verification for signature {signature.uuid}: {str(e)}')
                continue
        
        logger.info(f'Queued {count} signature(s) for verification')
        return {
            'success': True,
            'queued_count': count
        }
        
    except Exception as e:
        logger.error(f'Error queuing pending signature verifications: {str(e)}')
        raise

