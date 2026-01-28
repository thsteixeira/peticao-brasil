"""
URL configuration for signatures app.
"""
from django.urls import path
from . import views

app_name = 'signatures'

urlpatterns = [
    path('enviar/<uuid:uuid>/', views.SignatureSubmitView.as_view(), name='submit'),
    path('minhas-assinaturas/', views.MySignaturesView.as_view(), name='my_signatures'),
    path('peticao/<uuid:uuid>/assinaturas/', views.PetitionSignaturesView.as_view(), name='petition_signatures'),
    path('certificado/<uuid:uuid>/', views.DownloadCustodyCertificateView.as_view(), name='download_custody_certificate'),
    path('verificar-certificado/<uuid:uuid>/', views.VerifyCustodyCertificateView.as_view(), name='verify_custody_certificate'),
]
