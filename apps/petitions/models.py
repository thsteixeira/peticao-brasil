"""
Petition models for the Petição Brasil application.
"""
import uuid
import hashlib
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.text import slugify
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.postgres.search import SearchVector, SearchVectorField
from django.contrib.postgres.indexes import GinIndex
from django.db.models import Value
from apps.core.logging_utils import StructuredLogger, log_model_event

logger = StructuredLogger(__name__)


class Petition(models.Model):
    """
    A public petition created by a registered user.
    Can be signed by anyone (no login required to sign).
    """
    
    # Status choices
    STATUS_DRAFT = 'draft'
    STATUS_ACTIVE = 'active'
    STATUS_COMPLETED = 'completed'
    STATUS_EXPIRED = 'expired'
    STATUS_CLOSED = 'closed'
    STATUS_FLAGGED = 'flagged'
    
    STATUS_CHOICES = [
        (STATUS_DRAFT, 'Rascunho'),
        (STATUS_ACTIVE, 'Ativa'),
        (STATUS_COMPLETED, 'Concluída'),
        (STATUS_EXPIRED, 'Expirada'),
        (STATUS_CLOSED, 'Fechada'),
        (STATUS_FLAGGED, 'Sinalizada'),
    ]
    
    # Unique identifier
    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        verbose_name="UUID",
        help_text="Identificador único da petição"
    )
    
    # Creator (authenticated user required)
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='petitions_created',
        verbose_name="Criador",
        help_text="Usuário que criou a petição"
    )
    
    # Category
    category = models.ForeignKey(
        'core.Category',
        on_delete=models.PROTECT,
        related_name='petitions',
        verbose_name="Categoria",
        help_text="Categoria temática da petição"
    )
    
    # Content
    title = models.CharField(
        max_length=200,
        verbose_name="Título",
        help_text="Título da petição (máx. 200 caracteres)"
    )
    
    slug = models.SlugField(
        max_length=220,
        blank=True,
        verbose_name="Slug",
        help_text="URL amigável (gerado automaticamente)"
    )
    
    description = models.TextField(
        max_length=10000,
        verbose_name="Descrição",
        help_text="Descrição completa da causa (máx. 10.000 caracteres)"
    )
    
    # Goals
    signature_goal = models.PositiveIntegerField(
        validators=[MinValueValidator(10), MaxValueValidator(1000000)],
        verbose_name="Meta de assinaturas",
        help_text="Número de assinaturas desejadas (10 a 1.000.000)"
    )
    
    deadline = models.DateField(
        null=True,
        blank=True,
        verbose_name="Prazo",
        help_text="Data limite para coleta de assinaturas (opcional)"
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_ACTIVE,
        verbose_name="Status",
        help_text="Status atual da petição"
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name="Ativa",
        help_text="Se a petição está aceitando assinaturas"
    )
    
    # PDF and verification
    pdf_url = models.URLField(
        max_length=500,
        blank=True,
        verbose_name="URL do PDF",
        help_text="URL do PDF original da petição"
    )
    
    content_hash = models.CharField(
        max_length=64,
        blank=True,
        verbose_name="Hash do conteúdo",
        help_text="SHA-256 hash do conteúdo da petição para verificação"
    )
    
    # S3 file key for PDF
    pdf_file_key = models.CharField(
        max_length=500,
        blank=True,
        verbose_name="Chave do arquivo PDF",
        help_text="Chave do arquivo PDF no S3"
    )
    
    # Statistics
    signature_count = models.PositiveIntegerField(
        default=0,
        verbose_name="Assinaturas",
        help_text="Número de assinaturas verificadas"
    )
    
    view_count = models.PositiveIntegerField(
        default=0,
        verbose_name="Visualizações",
        help_text="Número de visualizações da página"
    )
    
    share_count = models.PositiveIntegerField(
        default=0,
        verbose_name="Compartilhamentos",
        help_text="Número de compartilhamentos em redes sociais"
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Criado em"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Atualizado em"
    )
    
    published_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Publicado em",
        help_text="Data de publicação da petição"
    )
    
    # Moderation
    moderation_notes = models.TextField(
        blank=True,
        verbose_name="Notas de moderação",
        help_text="Notas internas para moderadores"
    )
    
    # Full-text search
    search_vector = SearchVectorField(
        null=True,
        blank=True,
        verbose_name="Vetor de Busca",
        help_text="Campo de busca full-text (gerado automaticamente)"
    )
    
    class Meta:
        verbose_name = "Petição"
        verbose_name_plural = "Petições"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'is_active', '-created_at']),
            models.Index(fields=['category', '-created_at']),
            models.Index(fields=['creator', '-created_at']),
            models.Index(fields=['-signature_count']),
            models.Index(fields=['uuid']),
            models.Index(fields=['deadline']),
            GinIndex(fields=['search_vector'], name='petition_search_idx'),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(signature_goal__gte=10) & models.Q(signature_goal__lte=1000000),
                name='valid_signature_goal'
            ),
        ]
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        # Generate slug from title
        if not self.slug:
            base_slug = slugify(self.title)[:200]
            self.slug = base_slug
            
            # Ensure uniqueness
            counter = 1
            while Petition.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
                self.slug = f"{base_slug}-{counter}"
                counter += 1
        
        # Auto-publish if status is active and not yet published
        if self.status == self.STATUS_ACTIVE and not self.published_at:
            self.published_at = timezone.now()
        
        # Auto-expire if deadline passed
        if self.deadline and self.deadline < timezone.now().date():
            if self.status == self.STATUS_ACTIVE:
                self.status = self.STATUS_EXPIRED
                self.is_active = False
        
        # Auto-complete if goal reached
        if self.signature_count >= self.signature_goal:
            if self.status == self.STATUS_ACTIVE:
                self.status = self.STATUS_COMPLETED
        
        # Update search vector
        skip_search_update = kwargs.pop('skip_search_update', False)
        
        # Track if this is a new instance
        is_new = self.pk is None
        old_status = None
        
        if not is_new:
            # Get old status before save
            try:
                old_instance = Petition.objects.get(pk=self.pk)
                old_status = old_instance.status
            except Petition.DoesNotExist:
                pass
        
        super().save(*args, **kwargs)
        
        # Log lifecycle events
        if is_new:
            log_model_event(
                logger, 'Petition', 'created',
                self.uuid,
                title=self.title,
                creator_id=self.creator_id,
                category=self.category.name if self.category else None,
                status=self.status
            )
        elif old_status and old_status != self.status:
            log_model_event(
                logger, 'Petition', 'status_changed',
                self.uuid,
                old_status=old_status,
                new_status=self.status,
                signature_count=self.signature_count
            )
        
        if not skip_search_update:
            self.update_search_vector()
    
    def update_search_vector(self):
        """Update the search vector for full-text search"""
        # Get category name to avoid join in update query
        category_name = self.category.name if self.category else ''
        
        self.search_vector = (
            SearchVector(Value(self.title), weight='A', config='portuguese') + 
            SearchVector(Value(self.description), weight='B', config='portuguese') +
            SearchVector(Value(category_name), weight='C', config='portuguese')
        )
        Petition.objects.filter(pk=self.pk).update(search_vector=self.search_vector)
    
    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('petitions:detail', kwargs={'uuid': str(self.uuid), 'slug': self.slug})
    
    @property
    def progress_percentage(self):
        """Calculate percentage of goal reached"""
        if self.signature_goal == 0:
            return 0
        return min(100, int((self.signature_count / self.signature_goal) * 100))
    
    @property
    def days_remaining(self):
        """Calculate days until deadline"""
        if not self.deadline:
            return None
        delta = self.deadline - timezone.now().date()
        return max(0, delta.days)
    
    @property
    def is_expired(self):
        """Check if petition has expired"""
        if not self.deadline:
            return False
        return self.deadline < timezone.now().date()
    
    @property
    def is_successful(self):
        """Check if petition reached its goal"""
        return self.signature_count >= self.signature_goal
    
    def get_meta_title(self):
        """Generate SEO-optimized title"""
        return f"{self.title} | Petição Brasil"
    
    def get_meta_description(self):
        """Generate SEO-optimized description (max 160 chars)"""
        if len(self.description) <= 157:
            return self.description
        return self.description[:157] + "..."
    
    def get_og_image_url(self):
        """Get Open Graph image URL"""
        # TODO: Upload og-default.jpg to S3 or create category-specific OG images
        # For now, return None - OG image is optional
        return None
    
    def get_canonical_url(self):
        """Get canonical URL for SEO"""
        from django.conf import settings
        base_url = settings.SITE_URL.rstrip('/')
        return f"{base_url}{self.get_absolute_url()}"
    
    def get_signed_pdf_url(self):
        """
        Get a signed URL for the PDF file with expiration.
        Returns a secure, temporary URL that expires after 1 hour.
        """
        if not self.pdf_file_key and not self.pdf_url:
            return None
        
        from django.core.files.storage import default_storage
        
        # If we have the file key, generate signed URL
        if self.pdf_file_key:
            try:
                return default_storage.url(self.pdf_file_key)
            except Exception as e:
                logger.error('Failed to generate signed URL', extra={
                    'petition_id': self.id,
                    'petition_uuid': str(self.uuid),
                    'pdf_file_key': self.pdf_file_key,
                    'error': str(e)
                })
                # Fall back to pdf_url if it exists
                return self.pdf_url if self.pdf_url else None
        
        # Fallback to stored URL (for backwards compatibility)
        return self.pdf_url
    
    def increment_signature_count(self):
        """Safely increment signature count and check for milestones"""
        old_count = self.signature_count
        
        self.__class__.objects.filter(pk=self.pk).update(
            signature_count=models.F('signature_count') + 1
        )
        self.refresh_from_db()
        
        # Check if we hit a milestone (25%, 50%, 75%, 100%)
        old_progress = int((old_count / self.signature_goal) * 100)
        new_progress = int((self.signature_count / self.signature_goal) * 100)
        
        milestones = [25, 50, 75, 100]
        for milestone in milestones:
            if old_progress < milestone <= new_progress:
                # Hit a new milestone!
                try:
                    from apps.core.tasks import send_milestone_notification
                    send_milestone_notification.delay(self.id, milestone)
                except Exception as e:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"Failed to queue milestone email: {str(e)}")
    
    def increment_view_count(self):
        """Safely increment view count (atomic operation)"""
        self.__class__.objects.filter(pk=self.pk).update(
            view_count=models.F('view_count') + 1
        )
    
    def increment_share_count(self):
        """Safely increment share count (atomic operation)"""
        self.__class__.objects.filter(pk=self.pk).update(
            share_count=models.F('share_count') + 1
        )


class FlaggedContent(models.Model):
    """
    Reports of inappropriate or problematic petitions.
    Submitted by visitors (with or without login).
    """
    
    # Report reasons
    REASON_SPAM = 'spam'
    REASON_HATE = 'hate'
    REASON_MISINFO = 'misinfo'
    REASON_OFFTOPIC = 'offtopic'
    REASON_DUPLICATE = 'duplicate'
    REASON_OTHER = 'other'
    
    REASON_CHOICES = [
        (REASON_SPAM, 'Spam'),
        (REASON_HATE, 'Discurso de ódio'),
        (REASON_MISINFO, 'Desinformação'),
        (REASON_OFFTOPIC, 'Fora do tema'),
        (REASON_DUPLICATE, 'Duplicada'),
        (REASON_OTHER, 'Outro'),
    ]
    
    # Moderation status
    STATUS_PENDING = 'pending'
    STATUS_REVIEWING = 'reviewing'
    STATUS_APPROVED = 'approved'  # Report valid, action taken
    STATUS_DISMISSED = 'dismissed'  # Report invalid
    
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pendente'),
        (STATUS_REVIEWING, 'Em análise'),
        (STATUS_APPROVED, 'Procedente'),
        (STATUS_DISMISSED, 'Improcedente'),
    ]
    
    # Reported content
    petition = models.ForeignKey(
        'Petition',
        on_delete=models.CASCADE,
        related_name='flags',
        verbose_name="Petição",
        help_text="Petição denunciada"
    )
    
    # Reporter (optional - can be anonymous)
    reported_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reports_made',
        verbose_name="Denunciado por",
        help_text="Usuário que fez a denúncia (se logado)"
    )
    
    reporter_email = models.EmailField(
        blank=True,
        verbose_name="Email do denunciante",
        help_text="Email para contato (opcional)"
    )
    
    # Report details
    reason = models.CharField(
        max_length=20,
        choices=REASON_CHOICES,
        verbose_name="Motivo",
        help_text="Motivo da denúncia"
    )
    
    description = models.TextField(
        max_length=1000,
        blank=True,
        verbose_name="Descrição",
        help_text="Detalhes adicionais sobre a denúncia"
    )
    
    # Moderation
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        verbose_name="Status",
        help_text="Status da análise"
    )
    
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reports_reviewed',
        verbose_name="Analisado por",
        help_text="Moderador que analisou a denúncia"
    )
    
    review_notes = models.TextField(
        blank=True,
        verbose_name="Notas da análise",
        help_text="Notas do moderador sobre a análise"
    )
    
    action_taken = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Ação tomada",
        help_text="Ação realizada pelo moderador"
    )
    
    # Security
    ip_address_hash = models.CharField(
        max_length=64,
        blank=True,
        verbose_name="Hash do IP",
        help_text="Hash SHA-256 do endereço IP do denunciante"
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Criado em"
    )
    
    reviewed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Analisado em"
    )
    
    class Meta:
        verbose_name = "Conteúdo denunciado"
        verbose_name_plural = "Conteúdos denunciados"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['petition', 'status', '-created_at']),
            models.Index(fields=['status', '-created_at']),
        ]
    
    def __str__(self):
        return f"Denúncia: {self.petition.title} ({self.get_reason_display()})"
    
    @property
    def is_pending(self):
        return self.status == self.STATUS_PENDING
    
    def approve(self, moderator, action, notes=''):
        """Approve report and take action"""
        self.status = self.STATUS_APPROVED
        self.reviewed_by = moderator
        self.reviewed_at = timezone.now()
        self.action_taken = action
        self.review_notes = notes
        self.save()
    
    def dismiss(self, moderator, notes=''):
        """Dismiss report as invalid"""
        self.status = self.STATUS_DISMISSED
        self.reviewed_by = moderator
        self.reviewed_at = timezone.now()
        self.review_notes = notes
        self.save()
