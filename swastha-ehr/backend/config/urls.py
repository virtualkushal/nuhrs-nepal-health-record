from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include("core.urls")),
    path("api/fhir/v1/", include("core.fhir_urls")),
    # NUHRS federation adapter (NID-keyed FHIR, called by the National Platform).
    path("fhir/", include("core.nuhrs_urls")),
]



