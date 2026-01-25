"""
URL patterns for petitions app.
"""
from django.urls import path
from . import views

app_name = 'petitions'

urlpatterns = [
    path('', views.home_view, name='home'),
    path('help/how-to-sign/', views.how_to_sign_view, name='how_to_sign'),
    path('help/custody-certificate/', views.custody_certificate_view, name='custody_certificate'),
    path('about/', views.about_view, name='about'),
    path('terms/', views.terms_view, name='terms'),
    path('privacy/', views.privacy_policy_view, name='privacy_policy'),
    path('petitions/', views.PetitionListView.as_view(), name='list'),
    path('petitions/autocomplete/', views.petition_autocomplete, name='autocomplete'),
    path('petitions/create/', views.PetitionCreateView.as_view(), name='create'),
    path('petitions/<uuid:uuid>/<slug:slug>/', views.PetitionDetailView.as_view(), name='detail'),
    path('petitions/<uuid:uuid>/edit/', views.PetitionUpdateView.as_view(), name='edit'),
    path('petitions/<uuid:uuid>/share/', views.petition_share, name='share'),
    path('petitions/<uuid:uuid>/request-bulk-download/', views.RequestBulkDownloadView.as_view(), name='request_bulk_download'),
]
