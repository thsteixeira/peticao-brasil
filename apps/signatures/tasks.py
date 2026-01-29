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
        
        # Update status to processing + set timestamp
        signature.verification_status = Signature.STATUS_PROCESSING
        signature.processing_started_at = timezone.now()
        signature.save(update_fields=['verification_status', 'processing_started_at'])
        
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
            # Store certificate information
            if result['certificate_info']:
                cert_info = result['certificate_info']
                signature.certificate_info = cert_info
                signature.certificate_subject = cert_info.get('subject', '')
                signature.certificate_issuer = cert_info.get('issuer', '')
                signature.certificate_serial = cert_info.get('serial_number', '')
                signature.verified_cpf_from_certificate = result.get('cpf_verified', False)
            
            signature.verified = True
            signature.processing_completed_at = timezone.now()
            signature.save()
            
            # Approve signature (this increments the petition count)
            signature.approve()
            
            # Generate custody chain certificate
            try:
                from apps.signatures.custody_service import generate_custody_certificate
                certificate_url = generate_custody_certificate(signature, result)
                logger.info(
                    "Custody certificate generated",
                    signature_uuid=str(signature.uuid),
                    certificate_url=certificate_url
                )
            except Exception as cert_error:
                logger.error(
                    f"Failed to generate custody certificate: {str(cert_error)}",
                    signature_uuid=str(signature.uuid),
                    exc_info=True
                )
                # Don't fail the whole verification if certificate generation fails
            
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
                'status': 'approved',
                'custody_certificate_url': signature.custody_certificate_url
            }
        else:
            # Signature verification failed
            signature.verification_status = Signature.STATUS_REJECTED
            signature.rejection_reason = result.get('error', 'Verificação falhou')
            signature.processing_completed_at = timezone.now()
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
            
            # Check if this is a CNPJ rejection - send specific email
            if result.get('rejection_code') == 'CNPJ_NOT_ACCEPTED':
                try:
                    from apps.core.email import send_cnpj_rejection_email
                    send_cnpj_rejection_email(
                        signature=signature,
                        petition=signature.petition,
                        certificate_info=result.get('certificate_info', {})
                    )
                    logger.info(f"CNPJ rejection email sent for signature {signature.id}")
                except Exception as e:
                    logger.error(f"Failed to send CNPJ rejection email: {str(e)}")
            else:
                # Send generic rejection email notification
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


@shared_task(bind=True, max_retries=3)
def download_and_cache_crls(self):
    """
    Daily task to download CRLs from discovered endpoints and AC-Raiz.
    
    Downloads CRLs from:
    1. AC-Raiz (always)
    2. Previously discovered intermediate CA endpoints
    """
    import requests
    from datetime import datetime
    from cryptography import x509
    from cryptography.hazmat.backends import default_backend
    from django.core.cache import cache
    
    logger.info("Starting daily CRL download task")
    
    # Always include AC-Raiz
    CRL_ENDPOINTS = {
        'AC-Raiz': 'http://acraiz.icpbrasil.gov.br/LCRacraiz.crl',
    }
    
    # Load discovered endpoints from cache
    discovered_endpoints = cache.get('discovered_crl_endpoints', {})
    if discovered_endpoints:
        logger.info(f"Found {len(discovered_endpoints)} discovered CRL endpoints")
        CRL_ENDPOINTS.update(discovered_endpoints)
    
    results = {
        'success': [],
        'failed': [],
        'total_revoked_certs': 0,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    for ca_name, crl_url in CRL_ENDPOINTS.items():
        try:
            logger.info(f"Downloading CRL for {ca_name} from {crl_url}")
            
            # Download CRL
            response = requests.get(crl_url, timeout=60)
            response.raise_for_status()
            crl_data = response.content
            
            # Parse CRL
            try:
                crl = x509.load_der_x509_crl(crl_data, default_backend())
            except Exception:
                # Try PEM format
                crl = x509.load_pem_x509_crl(crl_data, default_backend())
            
            # Extract revoked certificate serial numbers
            revoked_serials = set()
            revoked_details = {}
            
            for revoked_cert in crl:
                serial = revoked_cert.serial_number
                revoked_serials.add(serial)
                
                # Store additional details
                revoked_details[str(serial)] = {
                    'revocation_date': revoked_cert.revocation_date_utc.isoformat(),
                    'reason': _get_revocation_reason(revoked_cert),
                }
            
            # Cache in Redis
            cache_key_serials = f"crl:{ca_name}:serials"
            cache_key_details = f"crl:{ca_name}:details"
            cache_key_meta = f"crl:{ca_name}:meta"
            
            # Cache for 25 hours (gives 1-hour overlap before next daily run)
            cache_timeout = 25 * 3600
            
            cache.set(cache_key_serials, revoked_serials, cache_timeout)
            cache.set(cache_key_details, revoked_details, cache_timeout)
            cache.set(cache_key_meta, {
                'this_update': crl.last_update_utc.isoformat(),
                'next_update': crl.next_update_utc.isoformat() if crl.next_update_utc else None,
                'issuer': crl.issuer.rfc4514_string(),
                'count': len(revoked_serials),
                'cached_at': datetime.utcnow().isoformat(),
            }, cache_timeout)
            
            results['success'].append(ca_name)
            results['total_revoked_certs'] += len(revoked_serials)
            
            logger.info(
                f"CRL cached for {ca_name}: {len(revoked_serials)} revoked certificates"
            )
            
        except Exception as e:
            logger.error(f"Failed to download/cache CRL for {ca_name}: {str(e)}")
            results['failed'].append({
                'ca': ca_name,
                'error': str(e)
            })
    
    # Log summary
    logger.info(
        f"CRL download task completed: "
        f"{len(results['success'])} successful, "
        f"{len(results['failed'])} failed, "
        f"{results['total_revoked_certs']} total revoked certificates cached"
    )
    
    return results


def _get_revocation_reason(revoked_cert):
    """Extract revocation reason from certificate."""
    try:
        from cryptography.x509.oid import CRLEntryExtensionOID
        reason_ext = revoked_cert.extensions.get_extension_for_oid(
            CRLEntryExtensionOID.CRL_REASON
        )
        return str(reason_ext.value.reason)
    except:
        return 'unspecified'


@shared_task(bind=True, max_retries=3)
def update_icp_brasil_certificates(self):
    """
    Daily task to check for new ICP-Brasil root certificates.
    
    Checks the official ICP-Brasil repository for new root certificates
    and downloads them if they don't already exist locally.
    """
    import os
    import urllib.request
    from datetime import datetime
    from django.conf import settings
    from cryptography import x509
    from cryptography.hazmat.backends import default_backend
    
    logger.info("Checking for ICP-Brasil certificate updates")
    
    # ICP-Brasil root certificates (keep updated)
    CERTIFICATE_URLS = {
        'ICP-Brasilv4.crt': 'https://acraiz.icpbrasil.gov.br/credenciadas/RAIZ/ICP-Brasilv4.crt',
        'ICP-Brasilv5.crt': 'https://acraiz.icpbrasil.gov.br/credenciadas/RAIZ/ICP-Brasilv5.crt',
        'ICP-Brasilv6.crt': 'https://acraiz.icpbrasil.gov.br/credenciadas/RAIZ/ICP-Brasilv6.crt',
        'ICP-Brasilv7.crt': 'https://acraiz.icpbrasil.gov.br/credenciadas/RAIZ/ICP-Brasilv7.crt',
        'ICP-Brasilv10.crt': 'https://acraiz.icpbrasil.gov.br/credenciadas/RAIZ/ICP-Brasilv10.crt',
        'ICP-Brasilv11.crt': 'https://acraiz.icpbrasil.gov.br/credenciadas/RAIZ/ICP-Brasilv11.crt',
        'ICP-Brasilv12.crt': 'https://acraiz.icpbrasil.gov.br/credenciadas/RAIZ/ICP-Brasilv12.crt',
        'ICP-Brasilv13.crt': 'https://acraiz.icpbrasil.gov.br/credenciadas/RAIZ/ICP-Brasilv13.crt',
        # Check periodically for v14, v15, etc.
        'ICP-Brasilv14.crt': 'https://acraiz.icpbrasil.gov.br/credenciadas/RAIZ/ICP-Brasilv14.crt',
        'ICP-Brasilv15.crt': 'https://acraiz.icpbrasil.gov.br/credenciadas/RAIZ/ICP-Brasilv15.crt',
    }
    
    cert_dir = os.path.join(
        settings.BASE_DIR,
        'apps',
        'signatures',
        'icp_certificates'
    )
    
    os.makedirs(cert_dir, exist_ok=True)
    
    results = {
        'downloaded': [],
        'skipped': [],
        'failed': [],
        'timestamp': datetime.utcnow().isoformat()
    }
    
    for filename, url in CERTIFICATE_URLS.items():
        filepath = os.path.join(cert_dir, filename)
        
        # Skip if file already exists
        if os.path.exists(filepath):
            results['skipped'].append(filename)
            continue
        
        try:
            logger.info(f"Downloading new ICP-Brasil certificate: {filename}")
            
            with urllib.request.urlopen(url, timeout=30) as response:
                cert_data = response.read()
            
            # Verify it's a valid certificate before saving
            try:
                x509.load_der_x509_certificate(cert_data, default_backend())
            except:
                x509.load_pem_x509_certificate(cert_data, default_backend())
            
            # Save certificate
            with open(filepath, 'wb') as f:
                f.write(cert_data)
            
            results['downloaded'].append(filename)
            logger.info(f"Downloaded new certificate: {filename}")
            
        except urllib.error.HTTPError as e:
            if e.code == 404:
                # Certificate doesn't exist yet (future version)
                pass
            else:
                results['failed'].append({
                    'filename': filename,
                    'error': str(e)
                })
        except Exception as e:
            logger.error(f"Failed to download {filename}: {str(e)}")
            results['failed'].append({
                'filename': filename,
                'error': str(e)
            })
    
    if results['downloaded']:
        logger.info(f"Downloaded {len(results['downloaded'])} new ICP-Brasil certificates")
    
    return results
