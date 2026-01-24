"""
PDF generation service using ReportLab.
Generates standardized petition PDFs for signing.
"""
import hashlib
import os
from io import BytesIO
from datetime import datetime

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib import colors
from reportlab.pdfgen import canvas


class PetitionPDFGenerator:
    """
    Generate PDF documents for petitions.
    """
    
    def __init__(self, petition):
        self.petition = petition
        self.buffer = BytesIO()
        self.width, self.height = A4
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Define custom paragraph styles."""
        # Title style
        self.styles.add(ParagraphStyle(
            name='PetitionTitle',
            parent=self.styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#1E40AF'),
            spaceAfter=20,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        # Header style
        self.styles.add(ParagraphStyle(
            name='Header',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#6B7280'),
            alignment=TA_CENTER,
            spaceAfter=30
        ))
        
        # Section heading
        self.styles.add(ParagraphStyle(
            name='SectionHeading',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#1F2937'),
            spaceAfter=10,
            spaceBefore=15,
            fontName='Helvetica-Bold'
        ))
        
        # Body text
        self.styles.add(ParagraphStyle(
            name='BodyJustified',
            parent=self.styles['Normal'],
            fontSize=11,
            alignment=TA_JUSTIFY,
            spaceAfter=12,
            leading=16
        ))
        
        # Footer
        self.styles.add(ParagraphStyle(
            name='Footer',
            parent=self.styles['Normal'],
            fontSize=8,
            textColor=colors.HexColor('#9CA3AF'),
            alignment=TA_CENTER
        ))
        
        # UUID Box
        self.styles.add(ParagraphStyle(
            name='UUIDBox',
            parent=self.styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#4B5563'),
            alignment=TA_CENTER,
            spaceAfter=20
        ))
    
    def _add_header(self, elements):
        """Add document header."""
        header_text = f"""
        <b>{settings.SITE_NAME}</b><br/>
        Petição Pública - Assinatura Digital Gov.br<br/>
        Gerado em: {datetime.now().strftime('%d/%m/%Y às %H:%M')}
        """
        elements.append(Paragraph(header_text, self.styles['Header']))
    
    def _add_petition_info(self, elements):
        """Add petition information section."""
        # Title
        elements.append(Paragraph(self.petition.title, self.styles['PetitionTitle']))
        
        # Metadata table
        metadata = [
            ['Categoria:', self.petition.category.name],
            ['Criado por:', self.petition.creator.get_full_name() or self.petition.creator.username],
            ['Data de criação:', self.petition.created_at.strftime('%d/%m/%Y')],
            ['Meta de assinaturas:', f"{self.petition.signature_goal:,}".replace(',', '.')],
        ]
        
        if self.petition.deadline:
            metadata.append(['Prazo:', self.petition.deadline.strftime('%d/%m/%Y')])
        
        table = Table(metadata, colWidths=[4.5*cm, 12*cm])
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#4B5563')),
            ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#1F2937')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 20))
    
    def _add_description(self, elements):
        """Add petition description."""
        elements.append(Paragraph('Descrição da Causa', self.styles['SectionHeading']))
        
        # Split description into paragraphs
        paragraphs = self.petition.description.split('\n')
        for para in paragraphs:
            if para.strip():
                elements.append(Paragraph(para.strip(), self.styles['BodyJustified']))
        
        elements.append(Spacer(1, 20))
    
    def _add_uuid_box(self, elements):
        """Add UUID identification box."""
        uuid_text = f"""
        <b>IDENTIFICADOR ÚNICO DA PETIÇÃO</b><br/>
        UUID: {str(self.petition.uuid)}<br/>
        <i>Este código identifica unicamente esta petição e deve ser preservado na assinatura digital.</i>
        """
        
        # Create a box with border
        uuid_para = Paragraph(uuid_text, self.styles['UUIDBox'])
        uuid_table = Table([[uuid_para]], colWidths=[16*cm])
        uuid_table.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#3B82F6')),
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#EFF6FF')),
            ('PADDING', (0, 0), (-1, -1), 10),
        ]))
        
        elements.append(uuid_table)
        elements.append(Spacer(1, 20))
    
    def _add_signature_instructions(self, elements):
        """Add instructions for digital signature."""
        elements.append(Paragraph('Como Assinar Esta Petição', self.styles['SectionHeading']))
        
        instructions = """
        <b>1.</b> Salve este arquivo PDF em seu computador<br/>
        <b>2.</b> Acesse o sistema de assinatura digital Gov.br (https://gov.br/assinador)<br/>
        <b>3.</b> Faça login com sua conta Gov.br (nível prata ou ouro)<br/>
        <b>4.</b> Selecione este arquivo PDF para assinar<br/>
        <b>5.</b> Escolha seu certificado digital ICP-Brasil<br/>
        <b>6.</b> Confirme a assinatura digital<br/>
        <b>7.</b> Baixe o arquivo PDF assinado<br/>
        <b>8.</b> Retorne ao site e faça o upload do PDF assinado para validação<br/>
        <br/>
        <i>IMPORTANTE: Não modifique o conteúdo deste PDF. Qualquer alteração invalidará a verificação.</i>
        """
        
        elements.append(Paragraph(instructions, self.styles['BodyJustified']))
        elements.append(Spacer(1, 20))
    
    def _add_footer(self, elements):
        """Add document footer."""
        footer_text = f"""
        {settings.SITE_NAME} - Plataforma de Petições Públicas<br/>
        {settings.SITE_URL}<br/>
        Documento gerado automaticamente - Não possui validade legal sem assinatura digital
        """
        elements.append(Spacer(1, 30))
        elements.append(Paragraph(footer_text, self.styles['Footer']))
    
    def generate(self):
        """
        Generate the PDF document.
        Returns the PDF as bytes.
        """
        # Create the PDF document
        doc = SimpleDocTemplate(
            self.buffer,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm,
            title=self.petition.title,
            author=f"{settings.SITE_NAME}",
            subject=f"Petição: {self.petition.title}",
        )
        
        # Build the document content
        elements = []
        
        self._add_header(elements)
        self._add_petition_info(elements)
        self._add_uuid_box(elements)
        self._add_description(elements)
        self._add_signature_instructions(elements)
        self._add_footer(elements)
        
        # Build PDF
        doc.build(elements)
        
        # Get PDF bytes
        pdf_bytes = self.buffer.getvalue()
        self.buffer.close()
        
        return pdf_bytes
    
    @staticmethod
    def calculate_content_hash(petition):
        """
        Calculate SHA-256 hash of petition content for verification.
        """
        content = f"{petition.uuid}|{petition.title}|{petition.description}|{petition.category.slug}"
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    @classmethod
    def generate_and_save(cls, petition):
        """
        Generate PDF and save to storage.
        Returns the file path/URL.
        """
        from apps.core.logging_utils import StructuredLogger
        logger = StructuredLogger(__name__)
        
        try:
            # Debug Django settings
            logger.info(f"DJANGO_SETTINGS_MODULE: {os.environ.get('DJANGO_SETTINGS_MODULE')}")
            logger.info(f"DEFAULT_FILE_STORAGE setting: {getattr(settings, 'DEFAULT_FILE_STORAGE', 'NOT SET')}")
            logger.info(f"AWS_STORAGE_BUCKET_NAME: {getattr(settings, 'AWS_STORAGE_BUCKET_NAME', 'NOT SET')}")
            logger.info(f"AWS_S3_REGION_NAME: {getattr(settings, 'AWS_S3_REGION_NAME', 'NOT SET')}")
            
            # Generate PDF
            generator = cls(petition)
            pdf_bytes = generator.generate()
            logger.info(f"PDF bytes generated: {len(pdf_bytes)} bytes")
            
            # Calculate content hash
            content_hash = cls.calculate_content_hash(petition)
            
            # Save to storage
            filename = f"petition_{petition.uuid}.pdf"
            filepath = os.path.join(settings.PETITION_PDF_STORAGE_PATH, filename)
            logger.info(f"Attempting to save to: {filepath}")
            logger.info(f"Storage backend class: {default_storage.__class__.__name__}")
            logger.info(f"Storage backend module: {default_storage.__class__.__module__}")
            logger.info(f"Storage backend full path: {default_storage.__class__.__module__}.{default_storage.__class__.__name__}")
            
            # Save using Django storage
            saved_path = default_storage.save(filepath, ContentFile(pdf_bytes))
            logger.info(f"File saved to path: {saved_path}")
            
            # Get URL (works for both local and S3 storage)
            if hasattr(default_storage, 'url'):
                pdf_url = default_storage.url(saved_path)
            else:
                pdf_url = f"{settings.MEDIA_URL}{saved_path}"
            
            logger.info(f"Generated PDF URL: {pdf_url}")
            
            # Update petition with PDF info
            petition.pdf_url = pdf_url
            petition.pdf_file_key = saved_path  # Store S3 key for signed URLs
            petition.content_hash = content_hash
            petition.save(update_fields=['pdf_url', 'pdf_file_key', 'content_hash'])
            
            return pdf_url
            
        except Exception as e:
            logger.error(f"Error saving PDF: {type(e).__name__}: {str(e)}")
            raise
