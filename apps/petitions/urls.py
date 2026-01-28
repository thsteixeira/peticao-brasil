"""
URL patterns for petitions app.
"""
from django.urls import path
from . import views

app_name = 'petitions'

urlpatterns = [
    path('', views.home_view, name='home'),
    path('ajuda/como-assinar/', views.how_to_sign_view, name='how_to_sign'),
    path('ajuda/certificado-custodia/', views.custody_certificate_view, name='custody_certificate'),
    path('sobre/', views.about_view, name='about'),
    path('termos/', views.terms_view, name='terms'),
    path('privacidade/', views.privacy_policy_view, name='privacy_policy'),
    path('peticoes/', views.PetitionListView.as_view(), name='list'),
    path('peticoes/autocomplete/', views.petition_autocomplete, name='autocomplete'),
    path('peticoes/criar/', views.PetitionCreateView.as_view(), name='create'),
    # More specific patterns must come before the general detail pattern
    path('peticoes/<uuid:uuid>/editar/', views.PetitionUpdateView.as_view(), name='edit'),
    path('peticoes/<uuid:uuid>/compartilhar/', views.petition_share, name='share'),
    path('peticoes/<uuid:uuid>/solicitar-download/', views.RequestBulkDownloadView.as_view(), name='request_bulk_download'),
    path('peticoes/<uuid:uuid>/<slug:slug>/', views.PetitionDetailView.as_view(), name='detail'),
]
