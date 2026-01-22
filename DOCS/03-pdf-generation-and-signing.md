# Democracia Direta - PDF Generation and Signing

**Project Phase:** Planning - Phase 3  
**Document Version:** 1.0  
**Last Updated:** November 23, 2025  
**Status:** Draft

---

## Table of Contents

1. [PDF Generation Overview](#pdf-generation-overview)
2. [Library Selection](#library-selection)
3. [PDF Document Structure](#pdf-document-structure)
4. [Content Hash Implementation](#content-hash-implementation)
5. [UUID Embedding Strategy](#uuid-embedding-strategy)
6. [Gov.br Signature Integration](#govbr-signature-integration)
7. [PDF Generation Service](#pdf-generation-service)
8. [Storage and Delivery](#storage-and-delivery)
9. [Error Handling](#error-handling)

---

## PDF Generation Overview

### Purpose

Generate a standardized PDF document for each petition that:
1. **Displays the petition content** in a professional, readable format
2. **Embeds unique identifiers** (UUID) for verification
3. **Contains metadata** for automated verification
4. **Is compatible with Gov.br signature system** (ICP-Brasil certificates)
5. **Can be verified** after being digitally signed

### Requirements

**Functional:**
- Generate PDF on petition creation (async)
- Include all petition details (title, description, metadata)
- Embed UUID in visible text and PDF metadata
- Calculate and store content hash
- Professional layout matching Pressiona branding

**Non-Functional:**
- Generation time < 5 seconds
- File size < 500KB
- Compatible with Gov.br signer
- PDF/A compliance (archival format)
- Accessible (screen reader compatible)

---

## Library Selection

### Chosen: ReportLab

**Library:** ReportLab 4.0+  
**License:** BSD (open source) with optional commercial license  
**Documentation:** https://www.reportlab.com/docs/reportlab-userguide.pdf

#### Pros:
✅ Industry standard for Python PDF generation  
✅ Precise control over layout and styling  
✅ Excellent support for Unicode (Portuguese characters)  
✅ Can embed metadata easily  
✅ Generates standard-compliant PDFs  
✅ Good performance for single-page documents  
✅ Well-documented and maintained  
✅ Compatible with digital signature tools  

#### Cons:
❌ Steeper learning curve than HTML-to-PDF solutions  
❌ Manual layout positioning required  
❌ Commercial license needed for some advanced features (we don't need them)

### Alternative Considered: WeasyPrint

**Library:** WeasyPrint 60+  
**Why not chosen:** Requires system dependencies (cairo, pango) which complicates Heroku deployment

### Installation

```bash
pip install reportlab==4.0.7
pip install pillow==10.1.0  # For image support
```

---

## PDF Document Structure

### Visual Layout

```
┌─────────────────────────────────────────────────────────┐
│                DEMOCRACIA DIRETA                       │
│            Plataforma de Petições Cidadãs            │
│                                                         │
│  Logo                                    [Categoria]    │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  PETIÇÃO PÚBLICA                                        │
│                                                         │
│  [TÍTULO DA PETIÇÃO EM DESTAQUE]                       │
│                                                         │
│  Categoria: [Nome]                                      │
│  Criado por: [Nome do Criador]                          │
│  Data: [DD/MM/YYYY]                                     │
│  Meta: [N] assinaturas                                  │
│                                                         │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  DESCRIÇÃO                                              │
│                                                         │
│  [Texto completo da descrição da petição,              │
│   formatado em parágrafos, respeitando quebras         │
│   de linha e espaçamento adequado para leitura]        │
│                                                         │
│                                                         │
│                                                         │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  COMO ASSINAR ESTA PETIÇÃO                             │
│                                                         │
│  1. Acesse: https://signer.estaleiro.serpro.gov.br/   │
│  2. Faça login com sua conta Gov.br                    │
│  3. Envie este PDF para assinatura                     │
│  4. Selecione assinatura Avançada ou Qualificada       │
│  5. Conclua o processo de assinatura                   │
│  6. Baixe o PDF assinado                               │
│  7. Envie o PDF assinado de volta em:                  │
│     https://democraciadireta.org/peticoes/[ID]/upload/ │
│                                                         │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Identificador da Petição: [UUID]                      │
│  Gerado em: [DD/MM/YYYY HH:MM]                         │
│                                                         │
│  Este documento deve ser assinado digitalmente         │
│  via Gov.br para garantir sua autenticidade.           │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### Page Configuration

```python
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm

# Page settings
PAGE_SIZE = A4  # 210mm x 297mm
PAGE_WIDTH = A4[0]
PAGE_HEIGHT = A4[1]

# Margins
MARGIN_TOP = 2 * cm
MARGIN_BOTTOM = 2 * cm
MARGIN_LEFT = 2 * cm
MARGIN_RIGHT = 2 * cm

# Content area
CONTENT_WIDTH = PAGE_WIDTH - MARGIN_LEFT - MARGIN_RIGHT
CONTENT_HEIGHT = PAGE_HEIGHT - MARGIN_TOP - MARGIN_BOTTOM
```

---

## Content Hash Implementation

### Hash Strategy

**What to hash:** Normalized petition text content (title + description)  
**Algorithm:** SHA-256 (256-bit hash = 64 hex characters)  
**Purpose:** Verify document content hasn't been altered between generation and signing  
**Additional:** Store original PDF for direct text comparison during verification

### Storage Requirements

When generating a petition PDF, the system must store:
1. **Original PDF file** - for text extraction during verification
2. **Content hash** - SHA-256 hash of normalized text
3. **Petition UUID** - embedded in PDF for identification

This allows the verification system to:
- Extract text from both the original PDF and the signed PDF
- Directly compare the two text strings to ensure no tampering
- Additionally validate using the content hash

### Normalization Rules

```python
def normalize_text(text):
    """
    Normalize text for consistent hashing.
    Removes variations that don't affect meaning.
    """
    import re
    
    # Convert to lowercase
    text = text.lower()
    
    # Replace multiple whitespace with single space
    text = re.sub(r'\s+', ' ', text)
    
    # Remove leading/trailing whitespace
    text = text.strip()
    
    # Remove punctuation that doesn't affect meaning
    # Keep: . , ! ? - (basic punctuation)
    # Remove: " ' ` (quotes that might vary)
    text = text.replace('"', '').replace("'", '').replace('`', '')
    
    # Normalize line breaks
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    
    return text
```

### Hash Calculation

```python
import hashlib

def calculate_content_hash(petition):
    """
    Calculate SHA-256 hash of petition content.
    
    Args:
        petition: Petition model instance
    
    Returns:
        str: 64-character hex string
    """
    # Combine title and description
    content = f"{petition.title}\n\n{petition.description}"
    
    # Normalize
    normalized = normalize_text(content)
    
    # Calculate hash
    hash_obj = hashlib.sha256(normalized.encode('utf-8'))
    content_hash = hash_obj.hexdigest()
    
    return content_hash
```

### Hash Storage

```python
# When generating PDF
petition.content_hash = calculate_content_hash(petition)
petition.save(update_fields=['content_hash'])
```

### Hash Verification (Later)

```python
def verify_content_hash(petition, extracted_text):
    """
    Verify extracted text matches stored hash.
    
    Args:
        petition: Petition model instance
        extracted_text: Text extracted from signed PDF
    
    Returns:
        bool: True if hash matches
    """
    # Normalize extracted text
    normalized = normalize_text(extracted_text)
    
    # Calculate hash of extracted text
    extracted_hash = hashlib.sha256(normalized.encode('utf-8')).hexdigest()
    
    # Compare with stored hash
    return extracted_hash == petition.content_hash
```

---

## UUID Embedding Strategy

### Dual Embedding Approach

**Strategy:** Embed petition UUID in **two places** for redundancy

1. **PDF Metadata** (machine-readable)
   - Custom metadata field: `/PetitionUUID`
   - Easy to extract programmatically
   - Survives most PDF transformations

2. **Visible Text** (human and machine-readable)
   - Printed at bottom of document
   - Visible verification
   - Backup if metadata is stripped

### Metadata Embedding

```python
from reportlab.pdfgen import canvas

def embed_metadata(pdf_canvas, petition):
    """
    Embed custom metadata in PDF.
    """
    # Standard metadata
    pdf_canvas.setTitle(petition.title)
    pdf_canvas.setAuthor(f"Democracia Direta - {petition.creator.get_full_name() or petition.creator.username}")
    pdf_canvas.setSubject(f"Petição Pública - {petition.category.name}")
    pdf_canvas.setCreator("DemocraciaDireta.org - Plataforma de Petições Cidadãs")
    
    # Custom metadata (accessible via PDF info dictionary)
    # Note: Custom fields use /Key format
    info = pdf_canvas._doc.info
    info.PetitionUUID = str(petition.uuid)
    info.PetitionID = str(petition.id)
    info.ContentHash = petition.content_hash
    info.GeneratedAt = petition.created_at.isoformat()
```

### Visible UUID Display

```python
def draw_footer_uuid(canvas, petition, y_position):
    """
    Draw UUID at bottom of page.
    """
    from reportlab.lib.colors import HexColor
    
    canvas.setFont("Courier", 8)
    canvas.setFillColor(HexColor('#666666'))
    
    uuid_text = f"Identificador da Petição: {petition.uuid}"
    
    # Center text
    text_width = canvas.stringWidth(uuid_text, "Courier", 8)
    x = (PAGE_WIDTH - text_width) / 2
    
    canvas.drawString(x, y_position, uuid_text)
```

### UUID Extraction (Later)

```python
from PyPDF2 import PdfReader

def extract_uuid_from_metadata(pdf_file):
    """
    Extract UUID from PDF metadata.
    """
    reader = PdfReader(pdf_file)
    metadata = reader.metadata
    
    if metadata and '/PetitionUUID' in metadata:
        return metadata['/PetitionUUID']
    
    return None


def extract_uuid_from_text(text):
    """
    Extract UUID from PDF text content.
    """
    import re
    
    # UUID pattern: 8-4-4-4-12 hexadecimal
    pattern = r'Identificador da Petição:\s*([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})'
    
    match = re.search(pattern, text, re.IGNORECASE)
    
    if match:
        return match.group(1)
    
    return None
```

---

## Gov.br Signature Integration

### Gov.br Signature System

**Official URL:** https://signer.estaleiro.serpro.gov.br/  
**Certificate Authority:** ICP-Brasil (Infraestrutura de Chaves Públicas Brasileira)  
**Signature Standard:** PAdES (PDF Advanced Electronic Signatures)

### How It Works

```
┌──────────────┐
│    User      │
└──────┬───────┘
       │ 1. Downloads unsigned PDF
       ▼
┌─────────────────────────────────────┐
│     Democracia Direta Platform       │
│  (Generates PDF with UUID/hash)     │
└──────────┬──────────────────────────┘
           │ 2. PDF file
           ▼
┌─────────────────────────────────────┐
│  Gov.br Signer (External Service)   │
│  https://signer.estaleiro.serpro... │
└──────────┬──────────────────────────┘
           │ 3. User logs in with Gov.br
           │ 4. Uploads PDF
           │ 5. Selects signature level
           │ 6. Authenticates
           │ 7. Gov.br adds signature layer
           ▼
┌─────────────────────────────────────┐
│       Signed PDF                    │
│  - Original content intact          │
│  - Digital signature layer added    │
│  - Certificate with CPF embedded    │
└──────────┬──────────────────────────┘
           │ 8. User downloads
           │ 9. User uploads to platform
           ▼
┌─────────────────────────────────────┐
│   Verification System              │
│  - Validates signature              │
│  - Extracts CPF from certificate    │
│  - Verifies content integrity       │
└─────────────────────────────────────┘
```

### Signature Levels (Gov.br)

| Level | Description | Requirements | Recommendation |
|-------|-------------|--------------|----------------|
| **Básica** | Simple electronic signature | Gov.br login (Level 1) | ❌ Not recommended - low security |
| **Avançada** | Advanced signature with qualified certificate | Gov.br login (Level 2+) + e-CPF | ✅ **Recommended** - good balance |
| **Qualificada** | Qualified signature with hardware token | Hardware certificate (e-CPF A3) | ✅ Accepted - highest security |

**Our Recommendation:** Accept **Avançada** or **Qualificada** only, reject **Básica**

### PDF Compatibility Requirements

For Gov.br compatibility, our PDF must:

✅ Use standard PDF 1.4+ format  
✅ Not be encrypted or password-protected  
✅ Not have existing digital signatures  
✅ Be under 10MB  
✅ Not use proprietary fonts (use standard fonts or embed fonts)  
✅ Have standard page size (A4 recommended)  

### What Gov.br Adds to the PDF

When a user signs via Gov.br, the system:

1. **Adds a signature field** to the PDF
2. **Embeds the digital certificate** containing:
   - Signer's full name
   - CPF number
   - Certificate issuer (CA)
   - Validity period
   - Public key
3. **Creates a cryptographic signature** of the document
4. **Adds visual signature** (optional, configurable by user)
5. **Increments PDF version** (e.g., 1.4 → 1.7)
6. **Adds signature timestamp**

**Important:** The original content remains intact, signature is a new layer.

---

## PDF Generation Service

### Service Class Structure

```python
# democracia_direta/services/pdf_generator.py

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.pdfgen import canvas
from io import BytesIO
import hashlib
from datetime import datetime


class PetitionPDFGenerator:
    """
    Generate standardized PDF documents for petitions.
    """
    
    # Brand colors
    PRIMARY_COLOR = HexColor('#0066CC')
    SECONDARY_COLOR = HexColor('#333333')
    ACCENT_COLOR = HexColor('#FF6B35')
    LIGHT_GRAY = HexColor('#F5F5F5')
    DARK_GRAY = HexColor('#666666')
    
    def __init__(self, petition):
        """
        Initialize generator with petition instance.
        
        Args:
            petition: Petition model instance
        """
        self.petition = petition
        self.buffer = BytesIO()
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Create custom paragraph styles"""
        
        # Title style
        self.styles.add(ParagraphStyle(
            name='PetitionTitle',
            parent=self.styles['Heading1'],
            fontSize=18,
            textColor=self.SECONDARY_COLOR,
            spaceAfter=20,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        # Metadata style
        self.styles.add(ParagraphStyle(
            name='Metadata',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=self.DARK_GRAY,
            spaceAfter=8,
            fontName='Helvetica'
        ))
        
        # Description style
        self.styles.add(ParagraphStyle(
            name='Description',
            parent=self.styles['Normal'],
            fontSize=11,
            textColor=self.SECONDARY_COLOR,
            spaceAfter=12,
            alignment=TA_JUSTIFY,
            fontName='Helvetica',
            leading=16
        ))
        
        # Section header style
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=self.PRIMARY_COLOR,
            spaceAfter=12,
            spaceBefore=20,
            fontName='Helvetica-Bold'
        ))
        
        # Instructions style
        self.styles.add(ParagraphStyle(
            name='Instructions',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=self.SECONDARY_COLOR,
            spaceAfter=8,
            fontName='Helvetica',
            leftIndent=20
        ))
        
        # Footer style
        self.styles.add(ParagraphStyle(
            name='Footer',
            parent=self.styles['Normal'],
            fontSize=8,
            textColor=self.DARK_GRAY,
            alignment=TA_CENTER,
            fontName='Courier'
        ))
    
    def generate(self):
        """
        Generate PDF and return as bytes.
        
        Returns:
            BytesIO: PDF file buffer
        """
        # Create PDF document
        doc = SimpleDocTemplate(
            self.buffer,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm,
            title=self.petition.title,
            author=f"Democracia Direta - {self.petition.creator.username}",
            subject=f"Petição Pública - {self.petition.category.name}",
        )
        
        # Build content
        story = []
        
        # Header
        story.extend(self._build_header())
        
        # Petition content
        story.extend(self._build_petition_content())
        
        # Instructions
        story.extend(self._build_instructions())
        
        # Footer metadata
        story.extend(self._build_footer_metadata())
        
        # Build PDF
        doc.build(story, onFirstPage=self._add_page_metadata)
        
        # Calculate and store content hash
        self._update_content_hash()
        
        # Reset buffer position
        self.buffer.seek(0)
        
        return self.buffer
    
    def _build_header(self):
        """Build PDF header with logo and platform info"""
        elements = []
        
        # Platform name
        header = Paragraph(
            "<b>DEMOCRACIA DIRETA</b><br/>"
            "<font size=10>Plataforma de Petições Cidadãs</font>",
            self.styles['Normal']
        )
        elements.append(header)
        elements.append(Spacer(1, 0.5*cm))
        
        # Category badge
        category_text = Paragraph(
            f"<font color='{self.petition.category.color}'>"
            f"<b>[{self.petition.category.name.upper()}]</b></font>",
            self.styles['Normal']
        )
        elements.append(category_text)
        elements.append(Spacer(1, 0.3*cm))
        
        # "Petição Pública" label
        label = Paragraph(
            "<b>PETIÇÃO PÚBLICA</b>",
            self.styles['Heading2']
        )
        elements.append(label)
        elements.append(Spacer(1, 0.5*cm))
        
        return elements
    
    def _build_petition_content(self):
        """Build main petition content"""
        elements = []
        
        # Title
        title = Paragraph(
            f"<b>{self.petition.title}</b>",
            self.styles['PetitionTitle']
        )
        elements.append(title)
        elements.append(Spacer(1, 0.3*cm))
        
        # Metadata table
        metadata_data = [
            ['Categoria:', self.petition.category.name],
            ['Criado por:', self.petition.creator.get_full_name() or self.petition.creator.username],
            ['Data:', self.petition.created_at.strftime('%d/%m/%Y')],
            ['Meta de assinaturas:', f"{self.petition.signature_goal:,}".replace(',', '.')],
        ]
        
        if self.petition.deadline:
            metadata_data.append([
                'Prazo:', 
                self.petition.deadline.strftime('%d/%m/%Y')
            ])
        
        metadata_table = Table(metadata_data, colWidths=[4*cm, 12*cm])
        metadata_table.setStyle(TableStyle([
            ('FONT', (0, 0), (0, -1), 'Helvetica-Bold', 9),
            ('FONT', (1, 0), (1, -1), 'Helvetica', 9),
            ('TEXTCOLOR', (0, 0), (-1, -1), self.DARK_GRAY),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        elements.append(metadata_table)
        elements.append(Spacer(1, 0.8*cm))
        
        # Separator line
        line_table = Table([['']], colWidths=[16*cm], rowHeights=[0.1*cm])
        line_table.setStyle(TableStyle([
            ('LINEABOVE', (0, 0), (-1, -1), 1, self.PRIMARY_COLOR),
        ]))
        elements.append(line_table)
        elements.append(Spacer(1, 0.5*cm))
        
        # Description section header
        desc_header = Paragraph(
            "<b>DESCRIÇÃO</b>",
            self.styles['SectionHeader']
        )
        elements.append(desc_header)
        
        # Description content (split into paragraphs)
        description_paragraphs = self.petition.description.split('\n\n')
        
        for para in description_paragraphs:
            if para.strip():
                # Replace single newlines with <br/> tags
                para_html = para.replace('\n', '<br/>')
                p = Paragraph(para_html, self.styles['Description'])
                elements.append(p)
        
        elements.append(Spacer(1, 1*cm))
        
        return elements
    
    def _build_instructions(self):
        """Build signing instructions"""
        elements = []
        
        # Section header
        header = Paragraph(
            "<b>COMO ASSINAR ESTA PETIÇÃO</b>",
            self.styles['SectionHeader']
        )
        elements.append(header)
        
        # Instructions
        instructions = [
            "1. Acesse o sistema de assinatura Gov.br:",
            "   <b>https://signer.estaleiro.serpro.gov.br/</b>",
            "",
            "2. Faça login com sua conta Gov.br (níveis Prata ou Ouro recomendados)",
            "",
            "3. Envie este arquivo PDF para assinatura",
            "",
            "4. Selecione o tipo de assinatura <b>Avançada</b> ou <b>Qualificada</b>",
            "   (NÃO utilize assinatura Básica)",
            "",
            "5. Conclua o processo de autenticação conforme solicitado",
            "",
            "6. Baixe o arquivo PDF assinado",
            "",
            "7. Retorne à plataforma Democracia Direta e envie o PDF assinado em:",
            f"   <b>https://democraciadireta.org/peticoes/{self.petition.id}/upload/</b>",
            "",
            "Após o envio, nosso sistema verificará automaticamente sua assinatura.",
        ]
        
        for instruction in instructions:
            p = Paragraph(instruction, self.styles['Instructions'])
            elements.append(p)
        
        elements.append(Spacer(1, 0.5*cm))
        
        # Warning box
        warning_data = [[
            Paragraph(
                "<b>⚠ IMPORTANTE:</b> Este documento deve ser assinado digitalmente "
                "via Gov.br para garantir sua autenticidade. Não aceitamos cópias "
                "impressas ou assinaturas manuscritas.",
                self.styles['Normal']
            )
        ]]
        
        warning_table = Table(warning_data, colWidths=[16*cm])
        warning_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), self.LIGHT_GRAY),
            ('BOX', (0, 0), (-1, -1), 1, self.DARK_GRAY),
            ('LEFTPADDING', (0, 0), (-1, -1), 12),
            ('RIGHTPADDING', (0, 0), (-1, -1), 12),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ]))
        
        elements.append(warning_table)
        elements.append(Spacer(1, 1*cm))
        
        return elements
    
    def _build_footer_metadata(self):
        """Build footer with petition identifiers"""
        elements = []
        
        # Separator line
        line_table = Table([['']], colWidths=[16*cm], rowHeights=[0.1*cm])
        line_table.setStyle(TableStyle([
            ('LINEABOVE', (0, 0), (-1, -1), 0.5, self.DARK_GRAY),
        ]))
        elements.append(line_table)
        elements.append(Spacer(1, 0.3*cm))
        
        # UUID
        uuid_text = Paragraph(
            f"<b>Identificador da Petição:</b> {self.petition.uuid}",
            self.styles['Footer']
        )
        elements.append(uuid_text)
        
        # Generation timestamp
        timestamp = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        timestamp_text = Paragraph(
            f"Gerado em: {timestamp}",
            self.styles['Footer']
        )
        elements.append(timestamp_text)
        
        # Verification note
        note = Paragraph(
            "Este documento é autêntico apenas quando assinado digitalmente via Gov.br",
            self.styles['Footer']
        )
        elements.append(note)
        
        return elements
    
    def _add_page_metadata(self, canvas, doc):
        """
        Add custom metadata to PDF.
        Called by ReportLab during PDF build.
        """
        # Standard metadata
        canvas.setTitle(self.petition.title)
        canvas.setAuthor(f"Democracia Direta - {self.petition.creator.username}")
        canvas.setSubject(f"Petição Pública - {self.petition.category.name}")
        canvas.setCreator("DemocraciaDireta.org - Plataforma de Petições Cidadãs")
        
        # Custom metadata fields
        info = canvas._doc.info
        info.PetitionUUID = str(self.petition.uuid)
        info.PetitionID = str(self.petition.id)
        info.CategorySlug = self.petition.category.slug
        info.GeneratedAt = datetime.now().isoformat()
        
        # Content hash will be added after generation
        if self.petition.content_hash:
            info.ContentHash = self.petition.content_hash
    
    def _update_content_hash(self):
        """
        Calculate and store content hash.
        Called after PDF generation.
        """
        # Combine title and description
        content = f"{self.petition.title}\n\n{self.petition.description}"
        
        # Normalize text
        normalized = self._normalize_text(content)
        
        # Calculate SHA-256 hash
        hash_obj = hashlib.sha256(normalized.encode('utf-8'))
        content_hash = hash_obj.hexdigest()
        
        # Store in petition model
        self.petition.content_hash = content_hash
        self.petition.save(update_fields=['content_hash'])
    
    @staticmethod
    def _normalize_text(text):
        """
        Normalize text for consistent hashing.
        """
        import re
        
        # Convert to lowercase
        text = text.lower()
        
        # Replace multiple whitespace with single space
        text = re.sub(r'\s+', ' ', text)
        
        # Remove leading/trailing whitespace
        text = text.strip()
        
        # Remove variable quotes
        text = text.replace('"', '').replace("'", '').replace('`', '')
        
        # Normalize line breaks
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        
        return text
```

---

## Storage and Delivery

### File Storage Strategy

**Storage Service:** AWS S3  
**Bucket Structure:**
```
s3://democracia-direta-petitions/
  ├── petitions/
  │   └── {petition.uuid}/
  │       └── original.pdf
  ├── signatures/
  │   └── {signature.uuid}/
  │       └── signed.pdf
  └── temp/
      └── {session-id}/
          └── upload.pdf
```

### S3 Configuration

```python
# democracia_direta/settings.py

# AWS S3 Settings
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = 'democracia-direta-petitions'
AWS_S3_REGION_NAME = 'sa-east-1'  # São Paulo
AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'
AWS_S3_OBJECT_PARAMETERS = {
    'CacheControl': 'max-age=86400',  # 24 hours
}
AWS_DEFAULT_ACL = 'private'  # Files are private by default
AWS_QUERYSTRING_AUTH = True  # Use signed URLs
AWS_QUERYSTRING_EXPIRE = 3600  # URLs expire in 1 hour

# Use S3 for media files (PDFs)
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
```

### Upload to S3

```python
# democracia_direta/services/pdf_generator.py (continued)

from django.core.files.base import ContentFile
from storages.backends.s3boto3 import S3Boto3Storage

class PetitionPDFGenerator:
    # ... previous methods ...
    
    def upload_to_s3(self):
        """
        Upload generated PDF to S3.
        
        Returns:
            str: Public URL of uploaded PDF
        """
        # Generate PDF
        pdf_buffer = self.generate()
        
        # Create S3 storage instance
        storage = S3Boto3Storage()
        
        # Generate file path
        filename = f"petitions/{self.petition.uuid}/original.pdf"
        
        # Upload to S3
        pdf_file = ContentFile(pdf_buffer.getvalue())
        path = storage.save(filename, pdf_file)
        
        # Get URL (signed URL for private files)
        url = storage.url(path)
        
        # Update petition model
        self.petition.pdf_url = url
        self.petition.save(update_fields=['pdf_url'])
        
        return url
```

### Download View

```python
# democracia_direta/views.py

from django.views import View
from django.http import HttpResponse, Http404
from django.shortcuts import get_object_or_404
from .models import Petition
import requests


class DownloadPetitionPDFView(View):
    """
    Download petition PDF (unsigned original).
    """
    
    def get(self, request, pk):
        # Get petition
        petition = get_object_or_404(
            Petition,
            pk=pk,
            is_active=True
        )
        
        # Check if PDF exists
        if not petition.pdf_url:
            raise Http404("PDF não disponível")
        
        # Increment view/download counter
        petition.increment_view_count()
        
        # For S3, redirect to signed URL
        # Or stream the file through Django (for privacy)
        
        # Option 1: Redirect (faster, uses S3 bandwidth)
        # return redirect(petition.pdf_url)
        
        # Option 2: Stream through Django (more control)
        response = requests.get(petition.pdf_url, stream=True)
        
        if response.status_code != 200:
            raise Http404("Erro ao baixar PDF")
        
        # Create HTTP response with PDF
        http_response = HttpResponse(
            response.content,
            content_type='application/pdf'
        )
        
        # Set filename for download
        filename = f"peticao-{petition.id}-{petition.slug[:30]}.pdf"
        http_response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return http_response
```

---

## Error Handling

### PDF Generation Errors

```python
# democracia_direta/tasks.py

from celery import shared_task
from .models import Petition
from .services.pdf_generator import PetitionPDFGenerator
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def generate_petition_pdf_task(self, petition_id):
    """
    Async task to generate petition PDF.
    
    Args:
        petition_id: ID of petition to generate PDF for
    """
    try:
        # Get petition
        petition = Petition.objects.get(id=petition_id)
        
        # Generate and upload PDF
        generator = PetitionPDFGenerator(petition)
        pdf_url = generator.upload_to_s3()
        
        logger.info(f"Generated PDF for petition {petition_id}: {pdf_url}")
        
        return {
            'success': True,
            'petition_id': petition_id,
            'pdf_url': pdf_url
        }
        
    except Petition.DoesNotExist:
        logger.error(f"Petition {petition_id} not found")
        return {'success': False, 'error': 'Petition not found'}
        
    except Exception as e:
        logger.error(f"Error generating PDF for petition {petition_id}: {str(e)}")
        
        # Retry task
        raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))


# Synchronous version (for MVP without Celery)
def generate_petition_pdf(petition):
    """
    Synchronous PDF generation (for MVP).
    """
    try:
        generator = PetitionPDFGenerator(petition)
        pdf_url = generator.upload_to_s3()
        return pdf_url
        
    except Exception as e:
        logger.error(f"Error generating PDF for petition {petition.id}: {str(e)}")
        raise
```

### Error Recovery

```python
# If PDF generation fails during petition creation

from django.db import transaction

def create_petition_with_pdf(form_data, user):
    """
    Create petition and generate PDF atomically.
    """
    try:
        with transaction.atomic():
            # Create petition
            petition = Petition.objects.create(
                creator=user,
                **form_data
            )
            
            # Generate PDF (synchronous for MVP)
            try:
                pdf_url = generate_petition_pdf(petition)
                petition.pdf_url = pdf_url
                petition.status = Petition.STATUS_ACTIVE
                petition.save()
                
            except Exception as pdf_error:
                # Log error but don't fail petition creation
                logger.error(f"PDF generation failed: {pdf_error}")
                
                # Mark petition as draft (PDF can be regenerated later)
                petition.status = Petition.STATUS_DRAFT
                petition.save()
                
                # Notify admins
                send_admin_notification(
                    f"PDF generation failed for petition {petition.id}"
                )
        
        return petition
        
    except Exception as e:
        logger.error(f"Failed to create petition: {e}")
        raise
```

### Retry Mechanism

```python
# Management command to regenerate failed PDFs

# democracia_direta/management/commands/regenerate_pdfs.py

from django.core.management.base import BaseCommand
from democracia_direta.models import Petition
from democracia_direta.services.pdf_generator import generate_petition_pdf


class Command(BaseCommand):
    help = 'Regenerate PDFs for petitions without PDF URL'

    def handle(self, *args, **options):
        # Find petitions without PDF
        petitions = Petition.objects.filter(pdf_url='')
        
        self.stdout.write(f"Found {petitions.count()} petitions without PDF")
        
        success_count = 0
        error_count = 0
        
        for petition in petitions:
            try:
                pdf_url = generate_petition_pdf(petition)
                success_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Generated PDF for petition {petition.id}')
                )
            except Exception as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(f'✗ Failed for petition {petition.id}: {str(e)}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\nComplete: {success_count} success, {error_count} errors'
            )
        )
```

---

## Testing Strategy

### Unit Tests

```python
# democracia_direta/tests/test_pdf_generator.py

from django.test import TestCase
from django.contrib.auth.models import User
from democracia_direta.models import Category, Petition
from democracia_direta.services.pdf_generator import PetitionPDFGenerator
from PyPDF2 import PdfReader
from io import BytesIO


class PDFGeneratorTestCase(TestCase):
    
    def setUp(self):
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com'
        )
        
        # Create test category
        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category'
        )
        
        # Create test petition
        self.petition = Petition.objects.create(
            creator=self.user,
            category=self.category,
            title='Test Petition',
            description='This is a test petition description.',
            signature_goal=100
        )
    
    def test_pdf_generation(self):
        """Test basic PDF generation"""
        generator = PetitionPDFGenerator(self.petition)
        pdf_buffer = generator.generate()
        
        # Check buffer is not empty
        self.assertGreater(len(pdf_buffer.getvalue()), 0)
    
    def test_pdf_contains_title(self):
        """Test PDF contains petition title"""
        generator = PetitionPDFGenerator(self.petition)
        pdf_buffer = generator.generate()
        
        # Read PDF
        reader = PdfReader(pdf_buffer)
        text = reader.pages[0].extract_text()
        
        # Check title is in PDF
        self.assertIn('Test Petition', text)
    
    def test_uuid_in_metadata(self):
        """Test UUID is embedded in PDF metadata"""
        generator = PetitionPDFGenerator(self.petition)
        pdf_buffer = generator.generate()
        
        # Read metadata
        reader = PdfReader(pdf_buffer)
        metadata = reader.metadata
        
        # Check UUID is present
        self.assertEqual(
            metadata.get('/PetitionUUID'),
            str(self.petition.uuid)
        )
    
    def test_content_hash_calculation(self):
        """Test content hash is calculated and stored"""
        generator = PetitionPDFGenerator(self.petition)
        generator.generate()
        
        # Refresh petition from DB
        self.petition.refresh_from_db()
        
        # Check hash exists and is 64 characters (SHA-256)
        self.assertIsNotNone(self.petition.content_hash)
        self.assertEqual(len(self.petition.content_hash), 64)
```

---

## Next Steps

1. ✅ Complete PDF generation documentation
2. ⏭️ Proceed to Phase 4: Signature Verification
3. ⏭️ Implement PDF generator service class
4. ⏭️ Set up S3 bucket and permissions
5. ⏭️ Create signing instructions page
6. ⏭️ Test PDF compatibility with Gov.br signer

---

**Document Status:** Complete. Ready for implementation and Phase 4 planning.
