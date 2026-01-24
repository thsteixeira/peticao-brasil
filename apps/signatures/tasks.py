"""
Celery tasks for signature verification.
"""
from celery import shared_task
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
import time
from apps.core.logging_utils import StructuredLogger

logger = StructuredLogger(__name__)


@shared_task(bind=True, max_retries=3)
def verify_signature(self, signature_id):
    """
    Async task to verify a signature's digital certificate.
    """
    start_time = time.time()
    try:
        from apps.signatures.models import Signature
        from apps.signatures.verification_service import PDFSignatureVerifier
        
        # Get signature
        signature = Signature.objects.get(id=signature_id)
        
        logger.info(
            "Starting signature verification",
            signature_id=signature_id,
            signature_uuid=str(signature.uuid),
            petition_id=signature.petition_id,
            task_id=self.request.id
        )
        
        # Update status to processing
        signature.verification_status = Signature.STATUS_PROCESSING
        signature.save(update_fields=['verification_status'])
        
        # Initialize verifier
        verifier = PDFSignatureVerifier()
        
        # Get PDF file content from storage (works with both S3 and local)
        try:
            signature.signed_pdf.open('rb')
            pdf_file = signature.signed_pdf
        except Exception as e:
            logger.error(f"Failed to open signed PDF: {str(e)}")
            raise
        
        # Verify the signature
        result = verifier.verify_pdf_signature(
            pdf_file,
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
            
            duration = time.time() - start_time
            logger.info(
                "Signature verified successfully",
                signature_id=signature_id,
                signature_uuid=str(signature.uuid),
                petition_id=signature.petition_id,
                duration_seconds=duration,
                task_id=self.request.id
            )
            
            # Send verification email notification
            try:
                from apps.core.tasks import send_signature_verified_notification
                send_signature_verified_notification.delay(signature.id)
            except Exception as e:
                logger.error(f"Failed to queue verification email: {str(e)}")
            
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
            
            duration = time.time() - start_time
            logger.warning(
                "Signature verification rejected",
                signature_id=signature_id,
                signature_uuid=str(signature.uuid),
                petition_id=signature.petition_id,
                rejection_reason=signature.rejection_reason,
                duration_seconds=duration,
                task_id=self.request.id
            )
            
            # Send rejection email notification
            try:
                from apps.core.tasks import send_signature_rejected_notification
                send_signature_rejected_notification.delay(signature.id)
            except Exception as e:
                logger.error(f"Failed to queue rejection email: {str(e)}")
            
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

