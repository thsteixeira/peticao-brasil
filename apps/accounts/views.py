"""
Views for user authentication and account management.
"""
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import CreateView, FormView
from django.urls import reverse_lazy
from django.contrib.auth.views import LoginView as DjangoLoginView, LogoutView as DjangoLogoutView
from django.utils.decorators import method_decorator

from .forms import UserRegistrationForm, UserLoginForm
from apps.core.rate_limiting import rate_limit, RateLimiters


class RegisterView(CreateView):
    """
    User registration view.
    """
    form_class = UserRegistrationForm
    template_name = 'accounts/register.html'
    success_url = reverse_lazy('petitions:home')
    
    def get_form_kwargs(self):
        """Pass request to form for Turnstile validation."""
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs
    
    def dispatch(self, request, *args, **kwargs):
        # Redirect if already logged in
        if request.user.is_authenticated:
            return redirect('petitions:home')
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        # Save the user
        response = super().form_valid(form)
        
        # Log the user in
        username = form.cleaned_data.get('username')
        password = form.cleaned_data.get('password1')
        user = authenticate(username=username, password=password)
        login(self.request, user)
        
        messages.success(
            self.request,
            f'Bem-vindo(a), {user.first_name}! Sua conta foi criada com sucesso.'
        )
        return response
    
    def form_invalid(self, form):
        messages.error(
            self.request,
            'Por favor, corrija os erros abaixo.'
        )
        return super().form_invalid(form)


class LoginView(DjangoLoginView):
    """
    User login view with rate limiting.
    """
    form_class = UserLoginForm
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True
    
    @method_decorator(rate_limit(max_requests=5, window=300))
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)
    
    def get_success_url(self):
        # Redirect to 'next' parameter or home
        next_url = self.request.GET.get('next')
        if next_url:
            return next_url
        return reverse_lazy('petitions:home')
    
    def form_valid(self, form):
        messages.success(
            self.request,
            f'Bem-vindo(a) de volta, {form.get_user().first_name}!'
        )
        return super().form_valid(form)
    
    def form_invalid(self, form):
        messages.error(
            self.request,
            'Nome de usuário ou senha incorretos.'
        )
        return super().form_invalid(form)


class LogoutView(DjangoLogoutView):
    """
    User logout view.
    """
    next_page = 'petitions:home'
    
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            messages.info(request, 'Você saiu da sua conta.')
        return super().dispatch(request, *args, **kwargs)


@login_required
def profile_view(request):
    """
    User profile view showing their petitions.
    """
    user_petitions = request.user.petitions_created.all()
    
    context = {
        'user_petitions': user_petitions,
        'total_signatures': sum(p.signature_count for p in user_petitions),
    }
    
    return render(request, 'accounts/profile.html', context)
