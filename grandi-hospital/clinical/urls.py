from django.urls import path

from . import views

urlpatterns = [
    path("whoami/", views.whoami),
    path("patients/", views.list_patients),
    path("conditions/", views.create_condition),
    path("observations/", views.create_observation),
]
