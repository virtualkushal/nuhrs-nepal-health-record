"""
FHIR adapter package.

Each hospital has its OWN named adapter class implementing ``BaseFHIRAdapter``.
``get_adapter()`` selects the correct one based on the configured
``SCHEMA_VARIANT`` so the rest of the codebase never needs an ``if variant``
switch — it just asks for "the adapter" and gets the right hospital's mapper.

    A -> MedicitiFHIRAdapter   (Nepal Mediciti Hospital)
    B -> NorvicFHIRAdapter     (Norvic International Hospital)
"""
from functools import lru_cache

from django.conf import settings

from .base_adapter import BaseFHIRAdapter
from .mediciti_adapter import MedicitiFHIRAdapter
from .norvic_adapter import NorvicFHIRAdapter

_REGISTRY = {
    "A": MedicitiFHIRAdapter,
    "B": NorvicFHIRAdapter,
}


@lru_cache(maxsize=None)
def get_adapter():
    """Return the singleton FHIR adapter for this hospital instance."""
    variant = getattr(settings, "SCHEMA_VARIANT", "A")
    adapter_cls = _REGISTRY.get(variant, MedicitiFHIRAdapter)
    return adapter_cls()


__all__ = [
    "BaseFHIRAdapter",
    "MedicitiFHIRAdapter",
    "NorvicFHIRAdapter",
    "get_adapter",
]
