from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("fhir/", include("lab.fhir_urls")),
    path("api/", include("lab.urls")),
]
