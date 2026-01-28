"""
URL patterns for accounts app.
"""
from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('entrar/', views.LoginView.as_view(), name='login'),
    path('sair/', views.LogoutView.as_view(), name='logout'),
    path('registrar/', views.RegisterView.as_view(), name='register'),
    path('perfil/', views.profile_view, name='profile'),
]
