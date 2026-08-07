from django.contrib import admin

from .models import (
    Allergy,
    Condition,
    Encounter,
    LabOrder,
    LabReport,
    LabResult,
    LocalPatient,
    MedicationRequest,
    Observation,
    Vitals,
)

admin.site.register(LocalPatient)
admin.site.register(Encounter)
admin.site.register(Condition)
admin.site.register(Observation)
admin.site.register(Allergy)
admin.site.register(Vitals)
admin.site.register(LabOrder)
admin.site.register(LabReport)
admin.site.register(LabResult)
admin.site.register(MedicationRequest)
