from django.contrib import admin

from .models import LabPatient, LabReport, LabResult

admin.site.register(LabPatient)
admin.site.register(LabReport)
admin.site.register(LabResult)
