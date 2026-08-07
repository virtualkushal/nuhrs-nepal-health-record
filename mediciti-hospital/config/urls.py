from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("fhir/", include("clinical.fhir_urls")),
    path("api/", include("clinical.urls")),
]
