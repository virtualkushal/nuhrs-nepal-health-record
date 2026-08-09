"""
Automatic NUHRS indexing.

Every time a clinical record is saved in SwasthyaEHR (diagnosis, lab result or
prescription), push its metadata pointer to the National Platform index so the
citizen's records become discoverable federation-wide immediately -- no manual
`nuhrs_push` run required.

Errors are swallowed (publish is best-effort) so a network blip never blocks a
local save. The boot-time `nuhrs_push` command remains as a catch-all re-sync.
"""

import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from core.models import Diagnosis, LabResult, Prescription
from core.nuhrs_publish import push_condition, push_medication, push_observation

logger = logging.getLogger(__name__)


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


@receiver(post_save, sender=Prescription)
def index_prescription(sender, instance, **kwargs):
    try:
        push_medication(instance)
    except Exception:
        logger.exception("Failed to index prescription %s", instance.id)