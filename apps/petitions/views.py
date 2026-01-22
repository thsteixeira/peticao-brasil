"""
Views for petition management.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.db.models import Q

from .models import Petition, FlaggedContent
from .forms import PetitionForm
from apps.core.models import Category


class PetitionListView(ListView):
    """
    Public view listing all active petitions.
    """
    model = Petition
    template_name = 'petitions/petition_list.html'
    context_object_name = 'petitions'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Petition.objects.filter(
            is_active=True,
            status='active'
        ).select_related('creator', 'category').order_by('-created_at')
        
        # Search functionality
        search = self.request.GET.get('q')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | Q(description__icontains=search)
            )
        
        # Category filter
        category_slug = self.request.GET.get('category')
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)
        
        # Sort options
        sort = self.request.GET.get('sort', 'recent')
        if sort == 'popular':
            queryset = queryset.order_by('-signature_count')
        elif sort == 'progress':
            queryset = queryset.order_by('-signature_count')
        elif sort == 'ending':
            queryset = queryset.filter(deadline__isnull=False).order_by('deadline')
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.filter(active=True)
        context['search_query'] = self.request.GET.get('q', '')
        context['current_category'] = self.request.GET.get('category', '')
        context['current_sort'] = self.request.GET.get('sort', 'recent')
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


class PetitionUpdateView(LoginRequiredMixin, UpdateView):
    """
    View for editing an existing petition (only by creator).
    """
    model = Petition
    form_class = PetitionForm
    template_name = 'petitions/petition_form.html'
    
    def get_object(self, queryset=None):
        uuid = self.kwargs.get('uuid')
        obj = get_object_or_404(Petition, uuid=uuid)
        
        # Only creator can edit
        if obj.creator != self.request.user:
            messages.error(self.request, 'Você não tem permissão para editar esta petição.')
            return redirect(obj.get_absolute_url())
        
        return obj
    
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
    
    return render(request, 'petitions/home.html', context)
