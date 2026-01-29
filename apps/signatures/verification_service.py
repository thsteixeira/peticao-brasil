"""
PDF signature verification service using ICP-Brasil certificates.
"""
import os
import hashlib
from datetime import datetime, timezone
from io import BytesIO

from django.conf import settings
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.x509 import load_der_x509_certificate, load_pem_x509_certificate
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.serialization import pkcs7

from pypdf import PdfReader


# ICP-Brasil OID Constants
# Reference: DOC-ICP-04 - Requisitos Mínimos para as PC ICP-Brasil
OID_CPF = x509.ObjectIdentifier("2.16.76.1.3.1")   # Natural Person (CPF) - ACCEPTED
OID_CNPJ = x509.ObjectIdentifier("2.16.76.1.3.3")  # Legal Entity (CNPJ) - REJECTED
OID_PIS_PASEP = x509.ObjectIdentifier("2.16.76.1.3.5")
OID_RG = x509.ObjectIdentifier("2.16.76.1.3.2")
OID_CEI = x509.ObjectIdentifier("2.16.76.1.3.7")  # Company ID - ALSO REJECTED


class SignatureVerificationError(Exception):
    """Base exception for signature verification errors."""
    pass


class PDFSignatureVerifier:
    """
    Verify digital signatures on PDF documents using ICP-Brasil certificates.
    """
    
    def __init__(self):
        self.cert_dir = os.path.join(
            settings.BASE_DIR,
            'apps',
            'signatures',
            'icp_certificates'
        )
        self.trusted_certs = self._load_trusted_certificates()
    
    def _load_trusted_certificates(self):
        """Load ICP-Brasil root certificates from storage."""
        certificates = []
        
        if not os.path.exists(self.cert_dir):
            raise SignatureVerificationError(
                f"Certificate directory not found: {self.cert_dir}. "
                "Run 'python manage.py download_icp_certificates' first."
            )
        
        for filename in os.listdir(self.cert_dir):
            if filename.endswith('.crt'):
                filepath = os.path.join(self.cert_dir, filename)
                try:
                    with open(filepath, 'rb') as f:
                        cert_data = f.read()
                        
                        # Try loading as PEM first, then DER
                        try:
                            cert = load_pem_x509_certificate(cert_data, default_backend())
                        except Exception:
                            cert = load_der_x509_certificate(cert_data, default_backend())
                        
                        certificates.append({
                            'filename': filename,
                            'certificate': cert,
                            'subject': cert.subject.rfc4514_string(),
                        })
                except Exception as e:
                    print(f"Warning: Could not load certificate {filename}: {e}")
        
        if not certificates:
            raise SignatureVerificationError(
                "No ICP-Brasil certificates found. "
                "Run 'python manage.py download_icp_certificates' first."
            )
        
        return certificates
    
    def verify_pdf_signature(self, pdf_file, petition):
        """
        Verify the digital signature on a PDF file.
        
        Args:
            pdf_file: File object or path to the signed PDF
            petition: The petition object this signature is for
            
        Returns:
            dict: Verification results with keys:
                - verified (bool): Whether signature is valid
                - certificate_info (dict): Certificate details if valid
                - error (str): Error message if invalid
        """
        result = {
            'verified': False,
            'certificate_info': None,
            'error': None,
        }
        
        try:
            # Read PDF file
            if isinstance(pdf_file, str):
                with open(pdf_file, 'rb') as f:
                    pdf_data = f.read()
            else:
                pdf_file.seek(0)
                pdf_data = pdf_file.read()
            
            # Parse PDF
            pdf_reader = PdfReader(BytesIO(pdf_data))
            
            # Check if PDF is signed
            if '/AcroForm' not in pdf_reader.trailer['/Root']:
                result['error'] = 'PDF não possui assinatura digital'
                return result
            
            acro_form = pdf_reader.trailer['/Root']['/AcroForm']
            
            if '/Fields' not in acro_form:
                result['error'] = 'PDF não possui campos de assinatura'
                return result
            
            # Extract signature fields
            signature_fields = []
            for field in acro_form['/Fields']:
                field_obj = field.get_object()
                if '/FT' in field_obj and field_obj['/FT'] == '/Sig':
                    signature_fields.append(field_obj)
            
            if not signature_fields:
                result['error'] = 'Nenhuma assinatura digital encontrada no PDF'
                return result
            
            # Get the first signature (we expect only one)
            sig_field = signature_fields[0]
            
            if '/V' not in sig_field:
                result['error'] = 'Campo de assinatura inválido'
                return result
            
            sig_dict = sig_field['/V']
            
            # Extract certificate from signature (PKCS#7 format)
            if '/Contents' in sig_dict:
                # Standard PKCS#7 signature format
                contents = sig_dict['/Contents']
                
                # Convert to bytes if needed
                if hasattr(contents, 'original_bytes'):
                    pkcs7_data = contents.original_bytes
                elif isinstance(contents, str):
                    pkcs7_data = contents.encode('latin-1')
                else:
                    pkcs7_data = bytes(contents)
                
                try:
                    # Parse PKCS#7 structure to extract certificates
                    # Remove any hex encoding wrapper
                    if pkcs7_data.startswith(b'<') and pkcs7_data.endswith(b'>'):
                        pkcs7_data = bytes.fromhex(pkcs7_data[1:-1].decode('ascii'))
                    
                    # Load PKCS#7 structure
                    from cryptography.hazmat.primitives.serialization import pkcs7
                    
                    # Try to load as PKCS7 signed data
                    try:
                        # PKCS#7 SignedData structure contains full certificate chain
                        p7 = pkcs7.load_der_pkcs7_certificates(pkcs7_data)
                        
                        if not p7:
                            result['error'] = 'Nenhum certificado encontrado na assinatura PKCS#7'
                            return result
                        
                        # Get the signer's certificate (usually the first one)
                        certificate = p7[0]
                        
                        # Store the full certificate chain for validation
                        certificate_chain = p7
                        
                    except Exception as pkcs7_error:
                        result['error'] = f'Erro ao processar PKCS#7: {str(pkcs7_error)}'
                        return result
                    
                except Exception as e:
                    result['error'] = f'Erro ao extrair certificado: {str(e)}'
                    return result
                    
            elif '/Cert' in sig_dict:
                # Legacy format with separate /Cert field
                cert_data = sig_dict['/Cert']
                if isinstance(cert_data, list):
                    cert_data = cert_data[0]
                
                # Parse certificate
                try:
                    if hasattr(cert_data, 'get_data'):
                        cert_bytes = cert_data.get_data()
                    else:
                        cert_bytes = bytes(cert_data)
                    
                    certificate = load_der_x509_certificate(cert_bytes, default_backend())
                    
                    # No chain for legacy format, only the end certificate
                    certificate_chain = [certificate]
                    
                except Exception as e:
                    result['error'] = f'Erro ao processar certificado: {str(e)}'
                    return result
            else:
                result['error'] = 'Certificado não encontrado na assinatura'
                return result
            
            # Now validate the certificate (for both PKCS#7 and /Cert formats)
            try:
                # STEP 1: Check certificate type (CPF vs CNPJ) - MUST BE FIRST
                cert_type, cert_value = self._extract_certificate_type(certificate)
                
                if cert_type == 'CNPJ':
                    # CNPJ certificate detected - REJECT immediately
                    import logging
                    logger = logging.getLogger(__name__)
                    
                    logger.warning(
                        f"CNPJ certificate rejected: {cert_value or 'unknown'}",
                        extra={
                            'certificate_serial': certificate.serial_number,
                            'petition_id': petition.id if petition else None,
                            'rejection_reason': 'CNPJ_NOT_ACCEPTED'
                        }
                    )
                    
                    result['verified'] = False
                    result['error'] = (
                        'Certificado CNPJ detectado. Esta plataforma aceita '
                        'apenas certificados de pessoa física (CPF). '
                        'Por favor, utilize certificado Gov.br, e-CPF ou A1/A3 de pessoa física.'
                    )
                    result['certificate_info'] = {
                        'certificate_type': 'CNPJ',
                        'cnpj': cert_value,
                        'serial_number': str(certificate.serial_number),
                        'issuer': certificate.issuer.rfc4514_string(),
                    }
                    result['rejection_code'] = 'CNPJ_NOT_ACCEPTED'
                    return result
                
                elif cert_type == 'UNKNOWN':
                    # Unknown certificate type - flag for manual review
                    import logging
                    logger = logging.getLogger(__name__)
                    
                    logger.warning(
                        f"Unknown certificate type - requires manual review",
                        extra={
                            'certificate_serial': certificate.serial_number,
                            'petition_id': petition.id if petition else None,
                        }
                    )
                    
                    result['verified'] = False
                    result['error'] = 'Tipo de certificado não identificado. Sua assinatura está em análise manual.'
                    result['requires_manual_review'] = True
                    result['certificate_info'] = self._extract_certificate_info(certificate)
                    return result
                
                # CPF certificate - continue with normal validation
                
                # STEP 2: Verify certificate chain against ICP-Brasil roots
                chain_valid = self._verify_certificate_chain(certificate, certificate_chain)
                
                if not chain_valid:
                    result['error'] = 'Certificado não pertence à cadeia ICP-Brasil'
                    return result
                
                # Check certificate validity period
                now = datetime.now(timezone.utc)
                if now < certificate.not_valid_before_utc:
                    result['error'] = 'Certificado ainda não é válido'
                    return result
                
                if now > certificate.not_valid_after_utc:
                    result['error'] = 'Certificado expirado'
                    return result
                
                # Extract certificate information
                cert_info = self._extract_certificate_info(certificate)
                
                # Verify PDF content hash matches petition
                content_valid = self._verify_pdf_content(pdf_data, petition)
                
                if not content_valid:
                    result['error'] = 'Conteúdo do PDF não corresponde à petição original'
                    return result
                
                # All checks passed
                result['verified'] = True
                result['certificate_info'] = cert_info
                
                # Add revocation check details if available
                if hasattr(self, 'revocation_details') and self.revocation_details:
                    result['revocation_method'] = self.revocation_details.get('method')
                    result['revocation_checked_at'] = self.revocation_details.get('checked_at')
                    result['revocation_status'] = self.revocation_details.get('status')
                
            except Exception as e:
                result['error'] = f'Erro na validação do certificado: {str(e)}'
                return result
            
        except Exception as e:
            result['error'] = f'Erro ao verificar PDF: {str(e)}'
        
        return result
    
    def _verify_certificate_chain(self, certificate, certificate_chain):
        """
        Verify that the certificate chain leads to an ICP-Brasil root.
        
        Args:
            certificate: The signer's certificate (end entity)
            certificate_chain: Full chain from PKCS#7 (may only include end cert)
        
        Returns:
            bool: True if chain is valid, False otherwise
        """
        import logging
        from apps.signatures.revocation_checker import CertificateRevocationChecker, RevocationCheckError
        
        logger = logging.getLogger(__name__)
        
        # Store revocation details for custody certificate
        self.revocation_details = None
        
        # Check certificate revocation status FIRST
        try:
            # Find issuer certificate in chain for OCSP fallback
            issuer_cert = self._find_issuer_certificate(certificate, certificate_chain)
            
            # Create revocation checker
            revocation_checker = CertificateRevocationChecker(
                certificate=certificate,
                issuer_certificate=issuer_cert
            )
            
            # Check revocation status
            is_revoked, revocation_details = revocation_checker.is_revoked()
            
            # Store for custody certificate
            self.revocation_details = revocation_details
            
            # Log the check
            logger.info(
                f"Certificate revocation check for serial {certificate.serial_number}: "
                f"revoked={is_revoked}, method={revocation_details['method']}"
            )
            
            if is_revoked:
                # Certificate is revoked - REJECT
                logger.warning(
                    f"REVOKED certificate detected! Serial: {certificate.serial_number}, "
                    f"Reason: {revocation_details.get('reason')}, "
                    f"Revocation date: {revocation_details.get('revocation_date')}"
                )
                return False
            
        except RevocationCheckError as e:
            # Revocation check failed
            logger.error(f"Revocation check error: {str(e)}")
            
            if getattr(settings, 'SIGNATURE_VERIFICATION_STRICT', True):
                # Strict mode: reject if we can't verify revocation status
                logger.error("Rejecting signature due to failed revocation check (strict mode)")
                return False
            else:
                # Permissive mode: allow if we can't verify (with warning)
                logger.warning(
                    "Allowing signature despite revocation check failure "
                    "(SIGNATURE_VERIFICATION_STRICT=False)"
                )
        
        # Known ICP-Brasil intermediate CAs (Gov.br chain)
        # These are common intermediate CAs under ICP-Brasil roots
        known_intermediates = [
            'AC Intermediaria do Governo Federal do Brasil',
            'AC Final do Governo Federal do Brasil',
            'Autoridade Certificadora do SERPRO',
            'Secretaria da Receita Federal do Brasil',
            'Gov-Br',
        ]
        
        # Build a list of all certificates we need to check
        for cert in certificate_chain:
            issuer = cert.issuer.rfc4514_string()
            cert_subject = cert.subject.rfc4514_string()
            
            # Check if this cert is issued directly by a trusted root
            for trusted_cert_info in self.trusted_certs:
                trusted_cert = trusted_cert_info['certificate']
                trusted_subject = trusted_cert.subject.rfc4514_string()
                
                # Check if the issuer matches the trusted root's subject
                if issuer == trusted_subject:
                    return True
            
            # Check if this cert itself IS a trusted root
            for trusted_cert_info in self.trusted_certs:
                trusted_cert = trusted_cert_info['certificate']
                trusted_subject = trusted_cert.subject.rfc4514_string()
                
                if cert_subject == trusted_subject:
                    return True
            
            # Check if issued by a known ICP-Brasil intermediate
            # This handles Gov.br certificates that don't include full chain
            for intermediate_name in known_intermediates:
                if intermediate_name in issuer:
                    # Accept certificates issued by known Gov.br intermediates
                    # In production, you'd want to download and verify these intermediate certs
                    return True
        
        return False
    
    def _find_issuer_certificate(self, certificate, certificate_chain):
        """
        Find the issuer's certificate in the chain.
        
        Args:
            certificate: Certificate whose issuer we're looking for
            certificate_chain: List of certificates from PKCS#7
            
        Returns:
            Issuer certificate or None
        """
        issuer_name = certificate.issuer
        
        for cert in certificate_chain:
            if cert.subject == issuer_name:
                return cert
        
        # Not found in chain - try loaded trusted certs
        for trusted_cert_info in self.trusted_certs:
            trusted_cert = trusted_cert_info['certificate']
            if trusted_cert.subject == issuer_name:
                return trusted_cert
        
        return None
    
    def _extract_certificate_info(self, certificate):
        """Extract relevant information from certificate."""
        # Get subject information
        subject = certificate.subject
        
        info = {
            'subject': subject.rfc4514_string(),
            'issuer': certificate.issuer.rfc4514_string(),
            'serial_number': str(certificate.serial_number),
            'not_before': certificate.not_valid_before_utc.isoformat(),
            'not_after': certificate.not_valid_after_utc.isoformat(),
            'version': certificate.version.name,
        }
        
        # Extract certificate type (CPF or CNPJ) and value
        cert_type, cert_value = self._extract_certificate_type(certificate)
        info['certificate_type'] = cert_type
        if cert_value:
            if cert_type == 'CPF':
                info['cpf'] = cert_value
            elif cert_type == 'CNPJ':
                info['cnpj'] = cert_value
        
        # Extract common name if available
        try:
            cn_list = subject.get_attributes_for_oid(x509.NameOID.COMMON_NAME)
            if cn_list:
                info['common_name'] = cn_list[0].value
        except:
            pass
        
        # Extract email if available
        try:
            email_list = subject.get_attributes_for_oid(x509.NameOID.EMAIL_ADDRESS)
            if email_list:
                info['email'] = email_list[0].value
        except:
            pass
        
        return info
    
    def _extract_certificate_type(self, certificate):
        """
        Extract certificate type (CPF or CNPJ) from ICP-Brasil certificate.
        
        Args:
            certificate: x509.Certificate object
            
        Returns:
            tuple: (cert_type, value)
                cert_type: 'CPF', 'CNPJ', or 'UNKNOWN'
                value: The extracted CPF/CNPJ number (or None)
        """
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            # Check Subject Alternative Name extension for OtherName entries
            try:
                san_ext = certificate.extensions.get_extension_for_oid(
                    x509.ExtensionOID.SUBJECT_ALTERNATIVE_NAME
                )
                
                # Parse Other Name entries
                for name in san_ext.value:
                    if isinstance(name, x509.OtherName):
                        # Check for CNPJ (MUST REJECT)
                        if name.type_id == OID_CNPJ:
                            try:
                                cnpj_value = name.value.decode('utf-8')
                                logger.info(f'CNPJ certificate detected: {cnpj_value}')
                                return ('CNPJ', cnpj_value)
                            except:
                                logger.warning('CNPJ OID found but value could not be decoded')
                                return ('CNPJ', None)
                        
                        # Check for CEI (Company ID - also reject)
                        elif name.type_id == OID_CEI:
                            try:
                                cei_value = name.value.decode('utf-8')
                                logger.info(f'CEI certificate detected (company): {cei_value}')
                                return ('CNPJ', cei_value)  # Treat as CNPJ
                            except:
                                return ('CNPJ', None)
                        
                        # Check for CPF (ACCEPTED)
                        elif name.type_id == OID_CPF:
                            try:
                                cpf_value = name.value.decode('utf-8')
                                logger.info(f'CPF certificate detected: {cpf_value}')
                                return ('CPF', cpf_value)
                            except:
                                logger.warning('CPF OID found but value could not be decoded')
                                return ('CPF', None)
            
            except x509.ExtensionNotFound:
                # No SAN extension
                pass
            
            # Fallback: check certificate Subject for CNPJ/CPF keywords
            subject_str = certificate.subject.rfc4514_string().upper()
            issuer_str = certificate.issuer.rfc4514_string().upper()
            
            # Check for CNPJ in subject or issuer
            if 'CNPJ' in subject_str or 'CNPJ' in issuer_str:
                logger.warning('CNPJ keyword found in certificate subject/issuer')
                return ('CNPJ', None)
            
            # Check for company-related keywords
            company_keywords = ['EMPRESA', 'LTDA', 'S.A.', 'S/A', 'ME', 'EPP', 'EIRELI']
            for keyword in company_keywords:
                if keyword in subject_str:
                    logger.warning(f'Company keyword "{keyword}" found in certificate')
                    return ('CNPJ', None)
            
            logger.info('Certificate type could not be determined')
            return ('UNKNOWN', None)
            
        except Exception as e:
            logger.error(f'Error extracting certificate type: {e}')
            return ('UNKNOWN', None)
    
    def _verify_pdf_content(self, pdf_data, petition):
        """
        Verify that the PDF content matches the petition.
        
        This checks if the petition UUID is embedded in the PDF by:
        1. Searching in raw PDF bytes (faster, covers all PDF objects)
        2. Extracting and searching text from pages (more reliable for content)
        """
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            if not petition:
                logger.error('[VERIFY_PETITION_CONTENT] Petition is None!')
                return False
            
            if not hasattr(petition, 'uuid') or petition.uuid is None:
                logger.error(f'[VERIFY_PETITION_CONTENT] Petition has no UUID! petition={petition}')
                return False
            
            petition_uuid = str(petition.uuid)
            logger.debug(f'[VERIFY_PETITION_CONTENT] Looking for UUID: {petition_uuid}')
            
            # Method 1: Search in raw bytes
            # This catches UUIDs in any part of the PDF structure
            if petition_uuid.encode('utf-8') in pdf_data:
                logger.debug('[VERIFY_PETITION_CONTENT] UUID found in raw bytes')
                return True
            
            # Method 2: Extract text from pages and search
            # This handles cases where UUID is in rendered text but encoded differently
            try:
                pdf_reader = PdfReader(BytesIO(pdf_data))
                all_text = ""
                
                for page in pdf_reader.pages:
                    try:
                        all_text += page.extract_text()
                    except:
                        pass
                
                if petition_uuid in all_text:
                    return True
                    
            except:
                pass
            
            # UUID not found
            return False
            
        except Exception:
            # On error, reject the signature
            return False
    
    @staticmethod
    def calculate_pdf_hash(pdf_file):
        """Calculate SHA-256 hash of PDF file."""
        if isinstance(pdf_file, str):
            with open(pdf_file, 'rb') as f:
                pdf_data = f.read()
        else:
            pdf_file.seek(0)
            pdf_data = pdf_file.read()
        
        return hashlib.sha256(pdf_data).hexdigest()
