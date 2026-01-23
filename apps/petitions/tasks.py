"""
Celery tasks for the petitions app.
"""
from celery import shared_task
from django.core.exceptions import ObjectDoesNotExist
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def generate_petition_pdf(self, petition_id):
    """
    Async task to generate PDF for a petition.
    """
    try:
        from apps.petitions.models import Petition
        from apps.petitions.pdf_service import PetitionPDFGenerator
        
        # Get petition
        petition = Petition.objects.get(id=petition_id)
        
        logger.info(f"Generating PDF for petition {petition.uuid}")
        
        # Generate and save PDF
        pdf_url = PetitionPDFGenerator.generate_and_save(petition)
        
        logger.info(f"PDF generated successfully for petition {petition.uuid}: {pdf_url}")
        
        return {
            'success': True,
            'petition_uuid': str(petition.uuid),
            'pdf_url': pdf_url
        }
        
    except ObjectDoesNotExist:
        logger.error(f"Petition with id {petition_id} not found")
        raise
    
    except Exception as exc:
        logger.error(f"Error generating PDF for petition {petition_id}: {str(exc)}")
        # Retry the task
        raise self.retry(exc=exc, countdown=60)


@shared_task(name='apps.petitions.tasks.cleanup_expired_petitions')
def cleanup_expired_petitions():
    """
    Daily task to mark expired petitions as closed.
    Runs at 2 AM daily via Celery Beat.
    """
    from apps.petitions.models import Petition
    from django.utils import timezone
    
    try:
        today = timezone.now().date()
        expired_petitions = Petition.objects.filter(
            status='active',
            deadline__lt=today
        )
        
        count = expired_petitions.count()
        if count > 0:
            expired_petitions.update(status='closed')
            logger.info(f'Closed {count} expired petition(s)')
        else:
            logger.info('No expired petitions to close')
            
        return {
            'success': True,
            'closed_count': count
        }
        
    except Exception as e:
        logger.error(f'Error cleaning up expired petitions: {str(e)}')
        raise


@shared_task
def cleanup_old_pdfs():
    """
    Periodic task to cleanup old/unused PDFs.
    """
    # TODO: Implement PDF cleanup logic
    pass

