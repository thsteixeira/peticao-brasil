"""
URL configuration for signatures app.
"""
from django.urls import path
from . import views

app_name = 'signatures'

urlpatterns = [
    path('submit/<uuid:uuid>/', views.SignatureSubmitView.as_view(), name='submit'),
    path('my-signatures/', views.MySignaturesView.as_view(), name='my_signatures'),
    path('petition/<uuid:uuid>/signatures/', views.PetitionSignaturesView.as_view(), name='petition_signatures'),
]
