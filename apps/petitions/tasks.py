"""
Celery tasks for the petitions app.
"""
from celery import shared_task
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
from django.core.files.base import ContentFile
from django.utils import timezone
import time
import zipfile
from io import BytesIO, StringIO
import csv
import requests
from apps.core.logging_utils import StructuredLogger, log_execution_time
from config.storage_backends import MediaStorage

logger = StructuredLogger(__name__)


@shared_task(bind=True, max_retries=3)
def generate_petition_pdf(self, petition_id):
    """
    Async task to generate PDF for a petition.
    """
    start_time = time.time()
    try:
        from apps.petitions.models import Petition
        from apps.petitions.pdf_service import PetitionPDFGenerator
        
        # Get petition
        petition = Petition.objects.get(id=petition_id)
        
        logger.info(
            "Starting PDF generation",
            petition_id=petition_id,
            petition_uuid=str(petition.uuid),
            task_id=self.request.id
        )
        
        # Generate and save PDF
        pdf_url = PetitionPDFGenerator.generate_and_save(petition)
        
        duration = time.time() - start_time
        logger.info(
            "PDF generated successfully",
            petition_id=petition_id,
            petition_uuid=str(petition.uuid),
            pdf_url=pdf_url,
            duration_seconds=duration,
            task_id=self.request.id
        )
        
        return {
            'success': True,
            'petition_uuid': str(petition.uuid),
            'pdf_url': pdf_url
        }
        
    except ObjectDoesNotExist:
        logger.error(
            "Petition not found",
            petition_id=petition_id,
            task_id=self.request.id
        )
        raise
    
    except Exception as exc:
        duration = time.time() - start_time
        logger.error(
            "PDF generation failed",
            petition_id=petition_id,
            error=str(exc),
            error_type=type(exc).__name__,
            duration_seconds=duration,
            retry_count=self.request.retries,
            task_id=self.request.id
        )
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


@shared_task(bind=True, max_retries=3)
def generate_bulk_download_package(self, petition_id, user_id, user_email):
    """
    Generate ZIP file with all signatures and send email with download link.
    
    Args:
        petition_id: ID of the petition
        user_id: ID of the requesting user
        user_email: Email to send download link
    """
    from apps.petitions.models import Petition
    from apps.signatures.models import Signature
    from apps.core.email import send_template_email
    from django.utils import timezone
    
    try:
        petition = Petition.objects.get(id=petition_id)
        
        # Get all approved signatures
        signatures = Signature.objects.filter(
            petition=petition,
            verification_status=Signature.STATUS_APPROVED
        ).select_related('petition').order_by('verified_at')
        
        if not signatures.exists():
            logger.warning(
                "No approved signatures found for bulk download",
                petition_id=petition_id
            )
            return
        
        logger.info(
            "Starting bulk download generation",
            petition_uuid=str(petition.uuid),
            signature_count=signatures.count(),
            user_id=user_id
        )
        
        # Create ZIP file in memory
        zip_buffer = BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Add manifest CSV
            manifest_csv = _generate_manifest_csv(signatures)
            zip_file.writestr('MANIFEST.csv', manifest_csv)
            
            # Add README
            readme_content = _generate_readme(petition, signatures.count())
            zip_file.writestr('README.txt', readme_content)
            
            # Process each signature
            for idx, signature in enumerate(signatures, 1):
                try:
                    # Download signed PDF
                    if signature.signed_pdf_url:
                        signed_pdf_name = f"{idx:04d}_signed_{signature.uuid}.pdf"
                        signed_pdf_data = _download_file(signature.signed_pdf_url)
                        if signed_pdf_data:
                            zip_file.writestr(
                                f"signed_pdfs/{signed_pdf_name}",
                                signed_pdf_data
                            )
                    
                    # Download custody certificate
                    if signature.custody_certificate_url:
                        cert_name = f"{idx:04d}_custody_{signature.uuid}.pdf"
                        cert_data = _download_file(signature.custody_certificate_url)
                        if cert_data:
                            zip_file.writestr(
                                f"custody_certificates/{cert_name}",
                                cert_data
                            )
                    
                except Exception as e:
                    logger.error(
                        f"Error adding signature {signature.uuid} to ZIP: {str(e)}"
                    )
                    # Add error note but continue
                    error_note = f"Erro ao processar assinatura {signature.uuid}: {str(e)}\n"
                    zip_file.writestr(
                        f"errors/{signature.uuid}.txt",
                        error_note
                    )
        
        # Upload ZIP to S3
        zip_buffer.seek(0)
        storage = MediaStorage()
        
        filename = f"bulk_downloads/assinaturas_{petition.uuid}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.zip"
        saved_path = storage.save(filename, ContentFile(zip_buffer.getvalue()))
        
        # Generate pre-signed URL (valid for 7 days)
        download_url = storage.url(saved_path, expire=604800)  # 7 days in seconds
        
        logger.info(
            "Bulk download package generated",
            petition_uuid=str(petition.uuid),
            user_id=user_id,
            zip_size_bytes=len(zip_buffer.getvalue()),
            download_url=download_url
        )
        
        # Send email with download link
        context = {
            'petition': petition,
            'signature_count': signatures.count(),
            'download_url': download_url,
            'expiration_days': 7,
            'site_url': settings.SITE_URL,
        }
        
        send_template_email(
            subject=f'Pacote de Assinaturas Pronto - {petition.title}',
            template_name='bulk_download_ready',
            context=context,
            recipient_list=[user_email],
        )
        
        logger.info(
            "Bulk download email sent",
            petition_uuid=str(petition.uuid),
            user_email=user_email
        )
        
        return {
            'success': True,
            'signature_count': signatures.count(),
            'download_url': download_url
        }
        
    except Exception as e:
        logger.error(
            f"Error generating bulk download: {str(e)}",
            petition_id=petition_id,
            exc_info=True
        )
        # Retry the task
        raise self.retry(exc=e, countdown=60)


def _download_file(url):
    """Download file from URL and return bytes."""
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.content
    except Exception as e:
        logger.error(f"Error downloading file from {url}: {str(e)}")
        return None


def _generate_manifest_csv(signatures):
    """Generate CSV manifest of all signatures."""
    output = StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow([
        'Número',
        'UUID da Assinatura',
        'Nome Completo',
        'CPF (hash)',
        'Data de Assinatura',
        'Data de Verificação',
        'Status',
        'Emissor do Certificado',
        'Número de Série',
        'Hash de Verificação',
        'URL PDF Assinado',
        'URL Certificado de Custódia'
    ])
    
    # Data rows - Only name and CPF hash exposed to petition creator
    # Email, city, state are NOT included for privacy protection
    for idx, sig in enumerate(signatures, 1):
        writer.writerow([
            idx,
            str(sig.uuid),
            sig.full_name,
            sig.cpf_hash,
            sig.signed_at.strftime('%d/%m/%Y %H:%M:%S') if sig.signed_at else '',
            sig.verified_at.strftime('%d/%m/%Y %H:%M:%S') if sig.verified_at else '',
            sig.get_verification_status_display(),
            sig.certificate_issuer,
            sig.certificate_serial,
            sig.verification_hash or '',
            sig.signed_pdf_url or '',
            sig.custody_certificate_url or ''
        ])
    
    return output.getvalue()


def _generate_readme(petition, signature_count):
    """Generate README file for the ZIP package."""
    return f"""
PETIÇÃO BRASIL - PACOTE DE ASSINATURAS
========================================

Petição: {petition.title}
UUID: {petition.uuid}
Data de Download: {timezone.now().strftime('%d/%m/%Y %H:%M:%S')}
Total de Assinaturas: {signature_count}

CONTEÚDO DESTE ARQUIVO
----------------------

1. MANIFEST.csv
   Planilha com todas as assinaturas e metadados

2. signed_pdfs/
   PDFs da petição assinados digitalmente pelos signatários

3. custody_certificates/
   Certificados de cadeia de custódia para cada assinatura

4. README.txt
   Este arquivo

SOBRE OS CERTIFICADOS DE CUSTÓDIA
----------------------------------

Cada assinatura possui um Certificado de Cadeia de Custódia que comprova:

- A verificação da assinatura digital ICP-Brasil
- A integridade do documento assinado
- A integridade do conteúdo da petição assinada
- A cronologia completa do processo de verificação
- O hash de verificação para detecção de adulteração

VERIFICAÇÃO DE AUTENTICIDADE
-----------------------------

Para verificar a autenticidade de qualquer certificado:

1. Acesse: {settings.SITE_URL}/assinaturas/verify-certificate/[UUID]
2. Compare o hash de verificação retornado com o hash no certificado
3. Se os hashes coincidirem, o certificado é autêntico e não foi alterado

IMPORTANTE
----------

- Estes documentos possuem valor legal como evidência
- Mantenha os arquivos em local seguro
- Não modifique os PDFs, pois isso invalidará as assinaturas digitais
- Os hashes de verificação garantem a integridade dos documentos
- Os certificados comprovam a integridade do texto da petição

Para mais informações:
{settings.SITE_URL}

Equipe Petição Brasil
""".strip()

