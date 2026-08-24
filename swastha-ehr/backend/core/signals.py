"""
Automatic NUHRS indexing.

Every time a clinical record is saved in SwasthyaEHR (encounter, diagnosis,
lab report, lab result or vitals), push its metadata pointer to the National
Platform index so the citizen's records become discoverable federation-wide
immediately -- no manual `nuhrs_push` run required.

Errors are swallowed (publish is best-effort) so a network blip never blocks a
local save. The boot-time `nuhrs_push` command remains as a catch-all re-sync.
"""

import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from core.models import Diagnosis, Encounter, LabReport, LabResult, Prescription, Vitals
from core.nuhrs_publish import (
    push_condition,
    push_encounter,
    push_lab_report,
    push_medication,
    push_observation,
    push_vitals,
)

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Encounter)
def index_encounter(sender, instance, **kwargs):
    try:
        push_encounter(instance)
    except Exception:
        logger.exception("Failed to index encounter %s", instance.id)


@receiver(post_save, sender=Diagnosis)
def index_diagnosis(sender, instance, **kwargs):
    try:
        push_condition(instance)
    except Exception:
        logger.exception("Failed to index diagnosis %s", instance.id)


@receiver(post_save, sender=LabResult)
def index_lab_result(sender, instance, **kwargs):
    try:
        push_observation(instance)
    except Exception:
        logger.exception("Failed to index lab result %s", instance.id)


@receiver(post_save, sender=LabReport)
def index_lab_report(sender, instance, **kwargs):
    try:
        push_lab_report(instance)
    except Exception:
        logger.exception("Failed to index lab report %s", instance.id)


@receiver(post_save, sender=Prescription)
def index_prescription(sender, instance, **kwargs):
    try:
        push_medication(instance)
    except Exception:
        logger.exception("Failed to index prescription %s", instance.id)


@receiver(post_save, sender=Vitals)
def index_vitals(sender, instance, **kwargs):
    try:
        push_vitals(instance)
    except Exception:
        logger.exception("Failed to index vitals %s", instance.id)