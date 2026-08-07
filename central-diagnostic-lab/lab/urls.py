from django.urls import path

from . import views

urlpatterns = [
    path("whoami/", views.whoami),
    path("patients/", views.list_patients),
    path("reports/", views.create_report),
]
