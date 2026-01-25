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
    path('certificate/<uuid:uuid>/', views.DownloadCustodyCertificateView.as_view(), name='download_custody_certificate'),
    path('verify-certificate/<uuid:uuid>/', views.VerifyCustodyCertificateView.as_view(), name='verify_custody_certificate'),
]
