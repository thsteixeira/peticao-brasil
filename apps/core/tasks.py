"""
Celery tasks for sending emails asynchronously.
"""
from celery import shared_task
from apps.core.email import (
    send_signature_verified_email,
    send_signature_rejected_email,
    send_petition_milestone_email
)
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def send_signature_verified_notification(self, signature_id):
    """
    Send email notification when signature is verified.
    """
    try:
        from apps.signatures.models import Signature
        
        signature = Signature.objects.get(id=signature_id)
        result = send_signature_verified_email(signature)
        
        logger.info(f'Verification email sent for signature {signature.uuid}')
        return {'success': True, 'sent': result}
        
    except Exception as exc:
        logger.error(f'Error sending verification email: {str(exc)}')
        raise self.retry(exc=exc, countdown=60)


@shared_task(bind=True, max_retries=3)
def send_signature_rejected_notification(self, signature_id):
    """
    Send email notification when signature is rejected.
    """
    try:
        from apps.signatures.models import Signature
        
        signature = Signature.objects.get(id=signature_id)
        result = send_signature_rejected_email(signature)
        
        logger.info(f'Rejection email sent for signature {signature.uuid}')
        return {'success': True, 'sent': result}
        
    except Exception as exc:
        logger.error(f'Error sending rejection email: {str(exc)}')
        raise self.retry(exc=exc, countdown=60)


@shared_task(bind=True, max_retries=3)
def send_milestone_notification(self, petition_id, milestone):
    """
    Send email notification when petition reaches milestone.
    """
    try:
        from apps.petitions.models import Petition
        
        petition = Petition.objects.get(id=petition_id)
        result = send_petition_milestone_email(petition, milestone)
        
        logger.info(f'Milestone {milestone}% email sent for petition {petition.uuid}')
        return {'success': True, 'sent': result}
        
    except Exception as exc:
        logger.error(f'Error sending milestone email: {str(exc)}')
        raise self.retry(exc=exc, countdown=60)
