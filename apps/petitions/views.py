"""  
Views for petition management.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.db.models import Q, F, Count
from django.contrib.postgres.search import SearchQuery, SearchRank
from django.utils import timezone
from datetime import timedelta
from django.http import JsonResponse
from django.views.generic import View
from django.core.exceptions import PermissionDenied
from apps.core.logging_utils import StructuredLogger

logger = StructuredLogger(__name__)

from .models import Petition, FlaggedContent
from .forms import PetitionForm
from .search import PetitionSearchForm
from apps.core.models import Category


class PetitionListView(ListView):
    """
    Public view listing all active petitions with advanced search and filters.
    """
    model = Petition
    template_name = 'petitions/petition_list.html'
    context_object_name = 'petitions'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Petition.objects.filter(
            is_active=True,
            status='active'
        ).select_related('creator', 'category')
        
        form = PetitionSearchForm(self.request.GET)
        
        if form.is_valid():
            # Text search with fallback for SQLite
            search_query = form.cleaned_data.get('q')
            if search_query:
                # Check if using PostgreSQL or SQLite
                from django.conf import settings
                from django.db import connection
                
                if connection.vendor == 'postgresql':
                    # Use PostgreSQL full-text search
                    search_query_obj = SearchQuery(search_query, config='portuguese')
                    queryset = queryset.filter(search_vector=search_query_obj)
                    queryset = queryset.annotate(
                        rank=SearchRank(F('search_vector'), search_query_obj)
                    ).order_by('-rank')
                else:
                    # Use basic SQLite search
                    queryset = queryset.filter(
                        Q(title__icontains=search_query) |
                        Q(description__icontains=search_query)
                    ).distinct()
            
            # Category filter (multiple)
            categories = form.cleaned_data.get('categories')
            if categories:
                queryset = queryset.filter(category__in=categories)
            
            # Status filter
            status = form.cleaned_data.get('status')
            if status == 'completed':
                queryset = queryset.filter(
                    signature_count__gte=F('signature_goal')
                )
            elif status == 'expiring_soon':
                # Petitions ending in the next 7 days
                expiring_date = timezone.now().date() + timedelta(days=7)
                queryset = queryset.filter(
                    deadline__isnull=False,
                    deadline__lte=expiring_date,
                    deadline__gte=timezone.now().date()
                )
            
            # Minimum signatures filter
            min_signatures = form.cleaned_data.get('min_signatures')
            if min_signatures is not None:
                queryset = queryset.filter(signature_count__gte=min_signatures)
            
            # Location filters (search in signatures)
            state = form.cleaned_data.get('state')
            if state:
                queryset = queryset.filter(
                    signatures__state=state
                ).annotate(
                    signature_from_state=Count('signatures')
                ).distinct()
            
            city = form.cleaned_data.get('city')
            if city:
                queryset = queryset.filter(
                    signatures__city__icontains=city
                ).distinct()
            
            # Sorting
            sort = form.cleaned_data.get('sort')
            if sort and sort != 'relevance':
                # If not search query, ignore relevance sort
                if not search_query and sort == 'relevance':
                    sort = '-created_at'
                queryset = queryset.order_by(sort)
            elif not search_query:
                # Default sort if no search
                queryset = queryset.order_by('-created_at')
        else:
            queryset = queryset.order_by('-created_at')
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = PetitionSearchForm(self.request.GET or None)
        context['categories'] = Category.objects.filter(active=True).order_by('order', 'name')
        return context


class PetitionDetailView(DetailView):
    """
    Public view showing petition details.
    """
    model = Petition
    template_name = 'petitions/petition_detail.html'
    context_object_name = 'petition'
    slug_field = 'slug'
    
    def get_object(self, queryset=None):
        # Get by UUID instead of pk
        uuid = self.kwargs.get('uuid')
        return get_object_or_404(Petition, uuid=uuid)
    
    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        # Increment view count
        self.object.increment_view_count()
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get recent signatures (approved only)
        context['recent_signatures'] = self.object.signatures.filter(
            verification_status='approved'
        ).order_by('-verified_at')[:10]
        
        # SEO meta tags
        context['meta_title'] = self.object.get_meta_title()
        context['meta_description'] = self.object.get_meta_description()
        context['og_title'] = self.object.title
        context['og_description'] = self.object.get_meta_description()
        context['og_image'] = self.object.get_og_image_url()
        context['og_type'] = 'article'
        context['og_url'] = self.object.get_canonical_url()
        context['canonical_url'] = self.object.get_canonical_url()
        
        return context


class PetitionCreateView(LoginRequiredMixin, CreateView):
    """
    View for creating a new petition (requires authentication).
    """
    model = Petition
    form_class = PetitionForm
    template_name = 'petitions/petition_form.html'
    
    def form_valid(self, form):
        # Set the creator to the current user
        form.instance.creator = self.request.user
        form.instance.status = 'active'
        
        response = super().form_valid(form)
        
        messages.success(
            self.request,
            f'Petição "{self.object.title}" criada com sucesso! O PDF será gerado em breve.'
        )
        
        # Trigger async PDF generation (with fallback for development)
        try:
            from .tasks import generate_petition_pdf
            generate_petition_pdf.delay(self.object.id)
        except Exception as e:
            # Fallback to synchronous generation if Celery is not available
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Celery not available, generating PDF synchronously: {e}")
            
            try:
                from .pdf_service import PetitionPDFGenerator
                PetitionPDFGenerator.generate_and_save(self.object)
            except Exception as pdf_error:
                logger.error(f"Failed to generate PDF: {pdf_error}")
        
        return response
    
    def get_success_url(self):
        return self.object.get_absolute_url()


def petition_autocomplete(request):
    """
    API endpoint for petition title autocomplete.
    Returns JSON with petition suggestions based on query.
    """
    query = request.GET.get('q', '').strip()
    
    if len(query) < 2:
        return JsonResponse({'results': []})
    
    # Search in titles with PostgreSQL full-text search
    search_query_obj = SearchQuery(query, config='portuguese')
    petitions = Petition.objects.filter(
        is_active=True,
        status='active',
        search_vector=search_query_obj
    ).annotate(
        rank=SearchRank(F('search_vector'), search_query_obj)
    ).select_related('category').order_by('-rank')[:10]
    
    results = []
    for petition in petitions:
        results.append({
            'id': str(petition.uuid),
            'title': petition.title,
            'category': petition.category.name,
            'signature_count': petition.signature_count,
            'url': petition.get_absolute_url()
        })
    
    return JsonResponse({'results': results})


class PetitionUpdateView(LoginRequiredMixin, UpdateView):
    """
    View for editing an existing petition (only by creator).
    """
    model = Petition
    form_class = PetitionForm
    template_name = 'petitions/petition_form.html'
    
    def get_object(self, queryset=None):
        uuid = self.kwargs.get('uuid')
        return get_object_or_404(Petition, uuid=uuid)
    
    def form_valid(self, form):
        messages.success(self.request, 'Petição atualizada com sucesso!')
        return super().form_valid(form)
    
    def get_success_url(self):
        return self.object.get_absolute_url()


def home_view(request):
    """
    Home page view with featured petitions.
    """
    featured_petitions = Petition.objects.filter(
        is_active=True,
        status='active'
    ).order_by('-signature_count')[:6]
    
    recent_petitions = Petition.objects.filter(
        is_active=True,
        status='active'
    ).order_by('-created_at')[:6]
    
    categories = Category.objects.filter(active=True)[:8]
    
    # Statistics
    total_petitions = Petition.objects.filter(status='active').count()
    total_signatures = sum(p.signature_count for p in Petition.objects.all())
    
    context = {
        'featured_petitions': featured_petitions,
        'recent_petitions': recent_petitions,
        'categories': categories,
        'total_petitions': total_petitions,
        'total_signatures': total_signatures,
    }
    
    return render(request, 'static_pages/home.html', context)


def how_to_sign_view(request):
    """Help page showing step-by-step guide for signing with Gov.br"""
    return render(request, 'help/how_to_sign.html')


def custody_certificate_view(request):
    """Help page explaining custody chain certificates"""
    return render(request, 'help/custody_certificate.html')


def about_view(request):
    """About page with platform information"""
    return render(request, 'static_pages/about.html')


def terms_view(request):
    """Terms of Use page"""
    return render(request, 'static_pages/terms.html')


def privacy_policy_view(request):
    """Privacy Policy page"""
    return render(request, 'static_pages/privacy.html')


def petition_share(request, uuid):
    """
    API endpoint to track petition shares and return share data.
    Returns JSON with share URLs and increments share count.
    """
    petition = get_object_or_404(Petition, uuid=uuid)
    
    # Increment share count
    petition.increment_share_count()
    
    # Build share URLs
    petition_url = request.build_absolute_uri(petition.get_absolute_url())
    share_text = f"{petition.title} - Petição Brasil"
    
    share_urls = {
        'whatsapp': f"https://wa.me/?text={share_text}%0A{petition_url}",
        'twitter': f"https://twitter.com/intent/tweet?text={share_text}&url={petition_url}",
        'facebook': f"https://www.facebook.com/sharer/sharer.php?u={petition_url}",
        'email': f"mailto:?subject={share_text}&body=Confira esta petição: {petition_url}",
        'url': petition_url
    }
    
    return JsonResponse({
        'success': True,
        'share_count': petition.share_count,
        'share_urls': share_urls
    })


class RequestBulkDownloadView(LoginRequiredMixin, View):
    """
    Request async generation of bulk download package.
    User will receive email with download link when ready.
    """
    
    def post(self, request, uuid):
        """Queue async task to generate ZIP file."""
        from apps.petitions.tasks import generate_bulk_download_package
        
        # Get petition
        petition = get_object_or_404(Petition, uuid=uuid)
        
        # Check permission - only creator can download
        if petition.creator != request.user:
            raise PermissionDenied("Apenas o criador da petição pode solicitar download.")
        
        # Check if petition has signatures
        if petition.signature_count == 0:
            messages.error(request, 'Esta petição ainda não possui assinaturas aprovadas.')
            return redirect('petitions:detail', uuid=uuid, slug=petition.slug)
        
        logger.info(
            "Bulk download requested",
            petition_uuid=str(petition.uuid),
            user_id=request.user.id,
            user_email=request.user.email
        )
        
        # Queue async task
        generate_bulk_download_package.delay(
            petition_id=petition.id,
            user_id=request.user.id,
            user_email=request.user.email
        )
        
        messages.success(
            request,
            'Seu pacote de assinaturas está sendo preparado. '
            'Você receberá um email com o link para download em alguns minutos.'
        )
        
        return redirect('petitions:detail', uuid=uuid, slug=petition.slug)
