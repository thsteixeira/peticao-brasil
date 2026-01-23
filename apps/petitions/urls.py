"""
URL patterns for petitions app.
"""
from django.urls import path
from . import views

app_name = 'petitions'

urlpatterns = [
    path('', views.home_view, name='home'),
    path('petitions/', views.PetitionListView.as_view(), name='list'),
    path('petitions/autocomplete/', views.petition_autocomplete, name='autocomplete'),
    path('petitions/create/', views.PetitionCreateView.as_view(), name='create'),
    path('petitions/<uuid:uuid>/<slug:slug>/', views.PetitionDetailView.as_view(), name='detail'),
    path('petitions/<uuid:uuid>/edit/', views.PetitionUpdateView.as_view(), name='edit'),
]
