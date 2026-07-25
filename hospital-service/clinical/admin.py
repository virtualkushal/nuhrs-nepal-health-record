from django.contrib import admin

from .models import Condition, Encounter, LocalPatient, Observation

admin.site.register(LocalPatient)
admin.site.register(Encounter)
admin.site.register(Condition)
admin.site.register(Observation)
