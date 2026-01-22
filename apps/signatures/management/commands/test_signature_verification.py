"""
Management command to test signature verification with detailed debug output.
"""
from django.core.management.base import BaseCommand
from apps.signatures.models import Signature
from apps.signatures.verification_service import PDFSignatureVerifier
import PyPDF2
import os


class Command(BaseCommand):
    help = 'Test signature verification with detailed debug output'

    def add_arguments(self, parser):
        parser.add_argument(
            'signature_uuid',
            type=str,
            help='UUID of the signature to verify'
        )
        parser.add_argument(
            '--show-pdf-structure',
            action='store_true',
            help='Show detailed PDF structure',
        )

    def handle(self, *args, **options):
        signature_uuid = options['signature_uuid']
        show_structure = options.get('show_pdf_structure', False)

        try:
            signature = Signature.objects.get(uuid=signature_uuid)
        except Signature.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Signature {signature_uuid} not found'))
            return

        self.stdout.write(self.style.SUCCESS(f'\n=== Testing Signature Verification ==='))
        self.stdout.write(f'Signature UUID: {signature.uuid}')
        self.stdout.write(f'Petition: {signature.petition.title}')
        self.stdout.write(f'Full Name: {signature.full_name}')
        self.stdout.write(f'Email: {signature.email}')
        self.stdout.write(f'Current Status: {signature.verification_status}')
        
        # Check if PDF file exists
        if not signature.signed_pdf:
            self.stdout.write(self.style.ERROR('\n✗ No PDF file attached to this signature'))
            return
        
        self.stdout.write(f'\nPDF File: {signature.signed_pdf.name}')
        self.stdout.write(f'PDF Size: {signature.signed_pdf.size} bytes')
        
        # Check if file exists
        if not signature.signed_pdf.storage.exists(signature.signed_pdf.name):
            self.stdout.write(self.style.ERROR('✗ PDF file does not exist in storage'))
            return
        
        self.stdout.write(self.style.SUCCESS('✓ PDF file exists'))
        
        # Read PDF structure
        self.stdout.write(f'\n=== Analyzing PDF Structure ===')
        try:
            signature.signed_pdf.open('rb')
            pdf_reader = PyPDF2.PdfReader(signature.signed_pdf)
            
            self.stdout.write(f'PDF Version: {pdf_reader.pdf_header if hasattr(pdf_reader, "pdf_header") else "Unknown"}')
            self.stdout.write(f'Number of pages: {len(pdf_reader.pages)}')
            self.stdout.write(f'Is encrypted: {pdf_reader.is_encrypted}')
            
            # Check for signature fields
            if show_structure:
                self.stdout.write('\n--- PDF Trailer ---')
                self.stdout.write(str(pdf_reader.trailer))
            
            # Check for AcroForm
            if '/Root' in pdf_reader.trailer:
                root = pdf_reader.trailer['/Root']
                self.stdout.write(f'\nRoot object type: {type(root)}')
                
                if hasattr(root, 'get_object'):
                    root_obj = root.get_object()
                else:
                    root_obj = root
                
                self.stdout.write(f'Root keys: {list(root_obj.keys()) if hasattr(root_obj, "keys") else "N/A"}')
                
                if '/AcroForm' in root_obj:
                    self.stdout.write(self.style.SUCCESS('\n✓ PDF has AcroForm (form fields)'))
                    acro_form = root_obj['/AcroForm']
                    
                    if hasattr(acro_form, 'get_object'):
                        acro_form_obj = acro_form.get_object()
                    else:
                        acro_form_obj = acro_form
                    
                    self.stdout.write(f'AcroForm keys: {list(acro_form_obj.keys()) if hasattr(acro_form_obj, "keys") else "N/A"}')
                    
                    if '/Fields' in acro_form_obj:
                        fields = acro_form_obj['/Fields']
                        self.stdout.write(f'Number of fields: {len(fields)}')
                        
                        # Look for signature fields
                        sig_count = 0
                        for i, field in enumerate(fields):
                            if hasattr(field, 'get_object'):
                                field_obj = field.get_object()
                            else:
                                field_obj = field
                            
                            field_type = field_obj.get('/FT', 'Unknown')
                            field_name = field_obj.get('/T', f'Field {i}')
                            
                            self.stdout.write(f'\n  Field {i}: {field_name}')
                            self.stdout.write(f'    Type: {field_type}')
                            
                            if field_type == '/Sig':
                                sig_count += 1
                                self.stdout.write(self.style.SUCCESS(f'    ✓ This is a signature field!'))
                                
                                if '/V' in field_obj:
                                    sig_dict = field_obj['/V']
                                    if hasattr(sig_dict, 'get_object'):
                                        sig_dict_obj = sig_dict.get_object()
                                    else:
                                        sig_dict_obj = sig_dict
                                    
                                    self.stdout.write(f'    Signature dict keys: {list(sig_dict_obj.keys()) if hasattr(sig_dict_obj, "keys") else "N/A"}')
                                    
                                    if '/Cert' in sig_dict_obj:
                                        self.stdout.write(self.style.SUCCESS('    ✓ Certificate found in signature!'))
                                        cert_data = sig_dict_obj['/Cert']
                                        self.stdout.write(f'    Certificate data type: {type(cert_data)}')
                                        if isinstance(cert_data, bytes):
                                            self.stdout.write(f'    Certificate size: {len(cert_data)} bytes')
                                    else:
                                        self.stdout.write(self.style.WARNING('    ⚠ No /Cert key in signature'))
                                else:
                                    self.stdout.write(self.style.WARNING('    ⚠ No /V (value) in signature field'))
                        
                        if sig_count == 0:
                            self.stdout.write(self.style.ERROR('\n✗ No signature fields found!'))
                        else:
                            self.stdout.write(self.style.SUCCESS(f'\n✓ Found {sig_count} signature field(s)'))
                    else:
                        self.stdout.write(self.style.ERROR('✗ AcroForm has no /Fields'))
                else:
                    self.stdout.write(self.style.ERROR('\n✗ PDF has no AcroForm'))
            else:
                self.stdout.write(self.style.ERROR('\n✗ PDF has no /Root'))
            
            signature.signed_pdf.close()
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n✗ Error reading PDF: {str(e)}'))
            import traceback
            self.stdout.write(traceback.format_exc())
        
        # Now run the actual verification
        self.stdout.write(f'\n=== Running Verification Service ===')
        try:
            verifier = PDFSignatureVerifier()
            self.stdout.write(f'Loaded {len(verifier.trusted_certs)} trusted ICP-Brasil certificates')
            
            for cert in verifier.trusted_certs:
                self.stdout.write(f'  - {cert["filename"]}: {cert["subject"]}')
            
            # Extract and display certificate chain details
            self.stdout.write('\n=== Certificate Chain Analysis ===')
            try:
                from cryptography.hazmat.primitives.serialization import pkcs7
                from io import BytesIO
                
                signature.signed_pdf.open('rb')
                pdf_data = signature.signed_pdf.read()
                signature.signed_pdf.close()
                
                pdf_reader = PyPDF2.PdfReader(BytesIO(pdf_data))
                
                if '/AcroForm' in pdf_reader.trailer['/Root']:
                    acro_form = pdf_reader.trailer['/Root']['/AcroForm']
                    if '/Fields' in acro_form:
                        for field in acro_form['/Fields']:
                            field_obj = field.get_object()
                            if '/FT' in field_obj and field_obj['/FT'] == '/Sig':
                                sig_dict = field_obj['/V']
                                
                                if '/Contents' in sig_dict:
                                    contents = sig_dict['/Contents']
                                    if hasattr(contents, 'original_bytes'):
                                        pkcs7_data = contents.original_bytes
                                    else:
                                        pkcs7_data = bytes(contents)
                                    
                                    if pkcs7_data.startswith(b'<'):
                                        pkcs7_data = bytes.fromhex(pkcs7_data[1:-1].decode('ascii'))
                                    
                                    p7_certs = pkcs7.load_der_pkcs7_certificates(pkcs7_data)
                                    
                                    self.stdout.write(f'Found {len(p7_certs)} certificate(s) in chain:\n')
                                    for i, cert in enumerate(p7_certs):
                                        self.stdout.write(f'  [{i+1}] Subject: {cert.subject.rfc4514_string()}')
                                        self.stdout.write(f'      Issuer:  {cert.issuer.rfc4514_string()}\n')
                                        
                                        # Check if matches trusted root
                                        for trusted in verifier.trusted_certs:
                                            if cert.subject.rfc4514_string() == trusted['certificate'].subject.rfc4514_string():
                                                self.stdout.write(self.style.SUCCESS(f'      ✓ IS trusted root: {trusted["filename"]}\n'))
                                                break
                                        else:
                                            # Check if issued by trusted root
                                            for trusted in verifier.trusted_certs:
                                                if cert.issuer.rfc4514_string() == trusted['certificate'].subject.rfc4514_string():
                                                    self.stdout.write(f'      → Issued by: {trusted["filename"]}\n')
                                                    break
                                    
                                    break
            except Exception as e:
                self.stdout.write(f'Chain extraction error: {e}\n')
            
            # Debug: Check what's actually in the PDF content
            self.stdout.write('\n=== PDF Content Analysis ===')
            try:
                signature.signed_pdf.open('rb')
                pdf_data = signature.signed_pdf.read()
                signature.signed_pdf.close()
                
                # Check for petition UUID
                petition_uuid = str(signature.petition.uuid)
                self.stdout.write(f'Looking for petition UUID: {petition_uuid}')
                
                if petition_uuid.encode() in pdf_data:
                    self.stdout.write(self.style.SUCCESS('✓ UUID found in raw PDF bytes'))
                else:
                    self.stdout.write(self.style.WARNING('⚠ UUID NOT found in raw PDF bytes'))
                
                # Try to extract readable text
                from PyPDF2 import PdfReader
                from io import BytesIO
                
                pdf_reader = PdfReader(BytesIO(pdf_data))
                all_text = ""
                for page_num, page in enumerate(pdf_reader.pages):
                    try:
                        page_text = page.extract_text()
                        all_text += page_text
                        if page_num == 0:
                            self.stdout.write(f'\nFirst page text (first 500 chars):')
                            self.stdout.write(page_text[:500] if page_text else '(no text extracted)')
                    except:
                        pass
                
                if petition_uuid in all_text:
                    self.stdout.write(self.style.SUCCESS('\n✓ UUID found in extracted text'))
                else:
                    self.stdout.write(self.style.WARNING('\n⚠ UUID NOT found in extracted text'))
                
                # Check for petition title
                if signature.petition.title:
                    self.stdout.write(f'\nLooking for petition title: {signature.petition.title[:50]}...')
                    if signature.petition.title in all_text:
                        self.stdout.write(self.style.SUCCESS('✓ Title found in extracted text'))
                    else:
                        self.stdout.write(self.style.WARNING('⚠ Title NOT found'))
                
            except Exception as e:
                self.stdout.write(f'Content analysis error: {e}')
            
            signature.signed_pdf.open('rb')
            result = verifier.verify_pdf_signature(signature.signed_pdf, signature.petition)
            signature.signed_pdf.close()
            
            self.stdout.write(f'\n=== Verification Result ===')
            if result['verified']:
                self.stdout.write(self.style.SUCCESS('✓ Signature VERIFIED'))
                self.stdout.write(f'\nCertificate Info:')
                for key, value in result.get('certificate_info', {}).items():
                    self.stdout.write(f'  {key}: {value}')
            else:
                self.stdout.write(self.style.ERROR('✗ Signature REJECTED'))
                self.stdout.write(f'Reason: {result.get("error", "Unknown error")}')
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n✗ Verification error: {str(e)}'))
            import traceback
            self.stdout.write(traceback.format_exc())
