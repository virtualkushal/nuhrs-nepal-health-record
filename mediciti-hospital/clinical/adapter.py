"""
Nepal Mediciti Hospital — FHIR R4 adapter.

This is the heart of the interoperability story. Mediciti stores its data using
its OWN column names (full_name, diagnosis_text, icd10_code, obs_type ...). This
adapter does two things:

  1. READ Mediciti's own columns  (the small, hospital-specific part)
  2. BUILD standard HL7 FHIR R4 resources from them  (the shared standard shape)

A different hospital (e.g. Norvic) has its OWN copy of this adapter that reads
ITS OWN differently-named columns but produces byte-for-byte the same FHIR shape.
That is the whole point of FHIR: heterogeneous local databases, one national
standard on the wire.

Everything the National Platform needs is produced here. Nothing outside this
file needs to know how Mediciti names its columns.
"""
from django.conf import settings

NID_SYSTEM = settings.NID_SYSTEM
ICD10_SYSTEM = "http://hl7.org/fhir/sid/icd-10"
LOINC_SYSTEM = "http://loinc.org"
RXNORM_SYSTEM = "http://www.nlm.nih.gov/research/umls/rxnorm"


class MedicitiFHIRAdapter:
    """Reads Mediciti's local schema and emits standard FHIR R4 resources."""

    source = settings.ORG_NAME

    # ------------------------------------------------------------------
    # Column readers — THIS is the Mediciti-specific mapping.
    # (Norvic's adapter reads different column names here.)
    # ------------------------------------------------------------------
    def patient_name(self, p):
        return p.full_name

    def encounter_fields(self, e):
        return {
            "clinician": e.doctor_name,
            "date": e.encounter_date,
            "category": e.encounter_type,
            "reason": e.reason,
        }

    def condition_fields(self, c):
        return {
            "text": c.diagnosis_text,
            "code": c.icd10_code,
            "status": c.clinical_status,
            "onset": c.onset_date,
        }

    def observation_fields(self, o):
        return {
            "name": o.obs_type,
            "value": o.value,
            "unit": o.unit,
            "date": o.observed_date,
        }

    # ------------------------------------------------------------------
    # Shared helpers
    # ------------------------------------------------------------------
    def _subject(self, nid):
        return {"identifier": {"system": NID_SYSTEM, "value": nid}}

    @staticmethod
    def _iso(d):
        return d.isoformat() if d else None

    @staticmethod
    def _is_number(s):
        try:
            float(s)
            return True
        except (TypeError, ValueError):
            return False

    # ------------------------------------------------------------------
    # FHIR builders — standard R4 output
    # ------------------------------------------------------------------
    def to_fhir_patient(self, p):
        res = {
            "resourceType": "Patient",
            "id": str(p.id),
            "identifier": [{"system": NID_SYSTEM, "value": p.nid}],
            "name": [{"text": self.patient_name(p)}],
            "gender": (p.gender or "").lower() or "unknown",
            "birthDate": self._iso(p.dob),
            "telecom": [{"system": "phone", "value": p.phone}] if p.phone else [],
            "_source": self.source,
        }
        if getattr(p, "mrn", ""):
            res["identifier"].append({"type": {"text": "MRN"}, "value": p.mrn})
        if getattr(p, "address", ""):
            res["address"] = [{"text": p.address}]
        if getattr(p, "marital_status", ""):
            res["maritalStatus"] = {"text": p.marital_status}
        if getattr(p, "blood_group", ""):
            res["extension"] = [{
                "url": "http://hl7.org/fhir/StructureDefinition/patient-bloodGroup",
                "valueString": p.blood_group,
            }]
        if getattr(p, "emergency_contact_name", ""):
            res["contact"] = [{
                "relationship": [{"text": "Emergency Contact"}],
                "name": {"text": p.emergency_contact_name},
                "telecom": [{"system": "phone", "value": p.emergency_contact_phone}] if p.emergency_contact_phone else [],
            }]
        return res

    def to_fhir_encounter(self, e):
        f = self.encounter_fields(e)
        return {
            "resourceType": "Encounter",
            "id": str(e.id),
            "status": "finished",
            "class": {"code": f["category"] or "AMB"},
            "subject": self._subject(e.patient.nid),
            "period": {"start": self._iso(f["date"])},
            "reasonCode": [{"text": f["reason"]}] if f["reason"] else [],
            "participant": [{"individual": {"display": f["clinician"]}}] if f["clinician"] else [],
            "_source": self.source,
        }

    def to_fhir_condition(self, c):
        f = self.condition_fields(c)
        return {
            "resourceType": "Condition",
            "id": str(c.id),
            "subject": self._subject(c.patient.nid),
            "code": {
                "coding": [{"system": ICD10_SYSTEM, "code": f["code"], "display": f["text"]}],
                "text": f["text"],
            },
            "clinicalStatus": {"coding": [{"code": (f["status"] or "active").lower()}]},
            "onsetDateTime": self._iso(f["onset"]),
            "_source": self.source,
        }

    def to_fhir_observation(self, o):
        f = self.observation_fields(o)
        return {
            "resourceType": "Observation",
            "id": str(o.id),
            "status": "final",
            "subject": self._subject(o.patient.nid),
            "code": {"text": f["name"]},
            "valueQuantity": {"value": f["value"], "unit": f["unit"]},
            "effectiveDateTime": self._iso(f["date"]),
            "_source": self.source,
        }

    def to_fhir_allergy(self, a):
        return {
            "resourceType": "AllergyIntolerance",
            "id": str(a.id),
            "patient": self._subject(a.patient.nid),
            "code": {"text": a.allergen},
            "reaction": [{
                "manifestation": [{"text": a.reaction}] if a.reaction else [],
                "severity": (a.severity or "").lower() or None,
            }] if (a.reaction or a.severity) else [],
            "recordedDate": self._iso(a.recorded_date),
            "clinicalStatus": {"coding": [{"code": "active"}]},
            "_source": self.source,
        }

    #: LOINC codes for the standard vital signs.
    _VITALS_LOINC = {
        "systolic_bp": ("8480-6", "Systolic blood pressure", "mmHg"),
        "diastolic_bp": ("8462-4", "Diastolic blood pressure", "mmHg"),
        "pulse": ("8867-4", "Heart rate", "beats/min"),
        "temperature": ("8310-5", "Body temperature", "Cel"),
        "spo2": ("59408-5", "Oxygen saturation", "%"),
        "respiratory_rate": ("9279-1", "Respiratory rate", "breaths/min"),
        "height_cm": ("8302-2", "Body height", "cm"),
        "weight_kg": ("29463-7", "Body weight", "kg"),
        "bmi": ("39156-5", "Body mass index", "kg/m2"),
    }

    def to_fhir_vitals(self, v):
        """A Vitals row expands into one Observation per recorded measurement."""
        out = []
        eff = self._iso(getattr(v, "recorded_date", None))
        for field, (code, display, unit) in self._VITALS_LOINC.items():
            val = getattr(v, field, None)
            if val is None:
                continue
            out.append({
                "resourceType": "Observation",
                "id": f"vital-{v.id}-{field}",
                "status": "final",
                "category": [{"coding": [{
                    "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                    "code": "vital-signs", "display": "Vital Signs",
                }]}],
                "code": {"coding": [{"system": LOINC_SYSTEM, "code": code, "display": display}], "text": display},
                "subject": self._subject(v.patient.nid),
                "effectiveDateTime": eff,
                "valueQuantity": {"value": float(val), "unit": unit, "system": "http://unitsofmeasure.org", "code": unit},
                "_source": self.source,
            })
        return out

    def to_fhir_lab_result(self, r):
        """A single analyte result -> laboratory Observation (LOINC-coded)."""
        obs = {
            "resourceType": "Observation",
            "id": f"labresult-{r.id}",
            "status": "final",
            "category": [{"coding": [{
                "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                "code": "laboratory", "display": "Laboratory",
            }]}],
            "code": {
                "coding": [{"system": LOINC_SYSTEM, "code": r.loinc_code, "display": r.test_name}] if r.loinc_code else [],
                "text": r.test_name,
            },
            "subject": self._subject(r.patient.nid),
            "effectiveDateTime": self._iso(r.report.report_date) if r.report_id else None,
            "valueString": r.value if not self._is_number(r.value) else None,
            "_source": self.source,
        }
        if self._is_number(r.value):
            obs.pop("valueString", None)
            obs["valueQuantity"] = {"value": float(r.value), "unit": r.unit}
        if r.reference_range:
            obs["referenceRange"] = [{"text": r.reference_range}]
        if r.interpretation:
            obs["interpretation"] = [{"coding": [{
                "system": "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation",
                "code": r.interpretation,
            }]}]
        return obs

    def to_fhir_diagnostic_report(self, report):
        """A lab panel report referencing its analyte Observations."""
        return {
            "resourceType": "DiagnosticReport",
            "id": f"labreport-{report.id}",
            "status": report.status or "final",
            "category": [{"coding": [{
                "system": "http://terminology.hl7.org/CodeSystem/v2-0074",
                "code": "LAB", "display": "Laboratory",
            }]}],
            "code": {"text": report.panel_name},
            "subject": self._subject(report.patient.nid),
            "effectiveDateTime": self._iso(report.report_date),
            "result": [{"reference": f"Observation/labresult-{res.id}"} for res in report.results.all()],
            "_source": self.source,
        }

    def to_fhir_medication(self, m):
        return {
            "resourceType": "MedicationRequest",
            "id": str(m.id),
            "status": "active",
            "intent": "order",
            "subject": self._subject(m.patient.nid),
            "medicationCodeableConcept": {
                "coding": [{"system": RXNORM_SYSTEM, "code": m.rxnorm_code, "display": m.medication_name}] if m.rxnorm_code else [],
                "text": m.medication_name,
            },
            "authoredOn": self._iso(m.prescribed_date),
            "requester": {"display": m.prescriber} if m.prescriber else None,
            "dosageInstruction": [{
                "text": f"{m.dosage} {m.frequency}".strip(),
                "route": {"text": m.route} if m.route else None,
                "timing": {"code": {"text": m.frequency}} if m.frequency else None,
            }],
            "_source": self.source,
        }

    # ------------------------------------------------------------------
    # Bundle helper
    # ------------------------------------------------------------------
    @staticmethod
    def make_bundle(resources):
        return {
            "resourceType": "Bundle",
            "type": "searchset",
            "total": len(resources),
            "entry": [{"resource": r} for r in resources],
        }
