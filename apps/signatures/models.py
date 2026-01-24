"""
Signature models for the Petição Brasil application.
"""
import uuid
import hashlib
from django.db import models
from django.utils import timezone
from django.core.validators import EmailValidator
from apps.core.logging_utils import StructuredLogger, log_model_event

# Import storage backend for S3
from config.storage_backends import MediaStorage

logger = StructuredLogger(__name__)


class Signature(models.Model):
    """
    A verified signature on a petition.
    Signer does NOT need to be a registered user.
    """
    
    # Verification status choices
    STATUS_PENDING = 'pending'
    STATUS_PROCESSING = 'processing'
    STATUS_APPROVED = 'approved'
    STATUS_REJECTED = 'rejected'
    STATUS_MANUAL_REVIEW = 'manual_review'
    
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pendente'),
        (STATUS_PROCESSING, 'Processando'),
        (STATUS_APPROVED, 'Aprovada'),
        (STATUS_REJECTED, 'Rejeitada'),
        (STATUS_MANUAL_REVIEW, 'Revisão Manual'),
    ]
    
    # Brazilian states
    STATES = [
        ('AC', 'Acre'), ('AL', 'Alagoas'), ('AP', 'Amapá'),
        ('AM', 'Amazonas'), ('BA', 'Bahia'), ('CE', 'Ceará'),
        ('DF', 'Distrito Federal'), ('ES', 'Espírito Santo'),
        ('GO', 'Goiás'), ('MA', 'Maranhão'), ('MT', 'Mato Grosso'),
        ('MS', 'Mato Grosso do Sul'), ('MG', 'Minas Gerais'),
        ('PA', 'Pará'), ('PB', 'Paraíba'), ('PR', 'Paraná'),
        ('PE', 'Pernambuco'), ('PI', 'Piauí'), ('RJ', 'Rio de Janeiro'),
        ('RN', 'Rio Grande do Norte'), ('RS', 'Rio Grande do Sul'),
        ('RO', 'Rondônia'), ('RR', 'Roraima'), ('SC', 'Santa Catarina'),
        ('SP', 'São Paulo'), ('SE', 'Sergipe'), ('TO', 'Tocantins'),
    ]
    
    # Unique identifier
    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        verbose_name="UUID",
        help_text="Identificador único da assinatura"
    )
    
    # Petition reference
    petition = models.ForeignKey(
        'petitions.Petition',
        on_delete=models.CASCADE,
        related_name='signatures',
        verbose_name="Petição",
        help_text="Petição assinada"
    )
    
    # Signer information (from verification form)
    full_name = models.CharField(
        max_length=200,
        verbose_name="Nome completo",
        help_text="Nome completo do signatário"
    )
    
    cpf_hash = models.CharField(
        max_length=64,
        verbose_name="Hash do CPF",
        help_text="Hash SHA-256 do CPF (não armazenamos CPF em texto)"
    )
    
    email = models.EmailField(
        validators=[EmailValidator()],
        verbose_name="Email",
        help_text="Email para confirmação"
    )
    
    city = models.CharField(
        max_length=100,
        verbose_name="Cidade",
        help_text="Cidade do signatário"
    )
    
    state = models.CharField(
        max_length=2,
        choices=STATES,
        verbose_name="Estado",
        help_text="Estado do signatário"
    )
    
    # PDF file
    signed_pdf = models.FileField(
        upload_to='signatures/pdfs/',
        storage=MediaStorage(),
        blank=True,
        null=True,
        verbose_name="PDF Assinado",
        help_text="Arquivo PDF assinado digitalmente"
    )
    
    signed_pdf_url = models.URLField(
        max_length=500,
        blank=True,
        verbose_name="URL do PDF assinado",
        help_text="URL do PDF assinado via Gov.br"
    )
    
    signed_pdf_size = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Tamanho do PDF",
        help_text="Tamanho do arquivo em bytes"
    )
    
    # Verification
    verification_status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        verbose_name="Status de verificação",
        help_text="Status da verificação automática"
    )
    
    verification_notes = models.TextField(
        blank=True,
        verbose_name="Notas de verificação",
        help_text="Detalhes do processo de verificação"
    )
    
    rejection_reason = models.TextField(
        blank=True,
        verbose_name="Motivo da rejeição",
        help_text="Motivo pelo qual a assinatura foi rejeitada"
    )
    
    verified_cpf_from_certificate = models.BooleanField(
        default=False,
        verbose_name="CPF verificado do certificado",
        help_text="Se o CPF foi extraído e validado do certificado digital"
    )
    
    certificate_info = models.JSONField(
        null=True,
        blank=True,
        verbose_name="Informações do certificado",
        help_text="Dados extraídos do certificado digital (JSON)"
    )
    
    # Privacy settings
    display_name_publicly = models.BooleanField(
        default=False,
        verbose_name="Exibir nome publicamente",
        help_text="Se True, exibe nome completo. Se False, apenas iniciais."
    )
    
    receive_updates = models.BooleanField(
        default=False,
        verbose_name="Receber atualizações",
        help_text="Aceita receber emails sobre o progresso da petição"
    )
    
    # Security and audit
    ip_address_hash = models.CharField(
        max_length=64,
        blank=True,
        verbose_name="Hash do IP",
        help_text="Hash SHA-256 do endereço IP (para auditoria)"
    )
    
    user_agent = models.CharField(
        max_length=500,
        blank=True,
        verbose_name="User Agent",
        help_text="Informações do navegador (para detecção de fraude)"
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Criado em",
        help_text="Quando a assinatura foi enviada"
    )
    
    signed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Assinado em",
        help_text="Data/hora extraída do certificado digital"
    )
    
    verified_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Verificado em",
        help_text="Quando a verificação foi concluída"
    )
    
    class Meta:
        verbose_name = "Assinatura"
        verbose_name_plural = "Assinaturas"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['petition', 'verification_status', '-created_at']),
            models.Index(fields=['verification_status', '-created_at']),
            models.Index(fields=['cpf_hash', 'petition']),  # Duplicate detection
            models.Index(fields=['email']),
        ]
        constraints = [
            # Ensure one signature per CPF per petition
            models.UniqueConstraint(
                fields=['petition', 'cpf_hash'],
                name='unique_cpf_per_petition'
            ),
        ]
    
    def __str__(self):
        return f"{self.full_name} - {self.petition.title}"
    
    @staticmethod
    def hash_cpf(cpf):
        """Hash a CPF for secure storage"""
        # Remove formatting
        cpf_clean = ''.join(filter(str.isdigit, cpf))
        # Hash with SHA-256
        return hashlib.sha256(cpf_clean.encode()).hexdigest()
    
    @staticmethod
    def hash_ip(ip_address):
        """Hash an IP address for secure storage"""
        return hashlib.sha256(ip_address.encode()).hexdigest()
    
    @property
    def display_name(self):
        """Return name for public display based on privacy setting"""
        if self.display_name_publicly:
            return self.full_name
        else:
            # Return initials (e.g., "João Silva" -> "J. S.")
            parts = self.full_name.split()
            if len(parts) == 1:
                return f"{parts[0][0]}."
            return f"{parts[0][0]}. {parts[-1][0]}."
    
    @property
    def is_verified(self):
        """Check if signature is verified"""
        return self.verification_status == self.STATUS_APPROVED
    
    def approve(self):
        """Approve signature and increment petition count"""
        if self.verification_status != self.STATUS_APPROVED:
            old_status = self.verification_status
            self.verification_status = self.STATUS_APPROVED
            self.verified_at = timezone.now()
            self.save()
            
            # Log approval event
            log_model_event(
                logger, 'Signature', 'approved',
                self.uuid,
                petition_id=self.petition_id,
                old_status=old_status,
                signer_name=self.full_name,
                city=self.city,
                state=self.state
            )
            
            # Increment petition signature count
            self.petition.increment_signature_count()
    
    def reject(self, reason):
        """Reject signature with reason"""
        old_status = self.verification_status
        self.verification_status = self.STATUS_REJECTED
        self.verification_notes = reason
        self.save()
        
        # Log rejection event
        log_model_event(
            logger, 'Signature', 'rejected',
            self.uuid,
            petition_id=self.petition_id,
            old_status=old_status,
            rejection_reason=reason,
            signer_name=self.full_name
        )
