"""
HL7 FHIR R4 serializers for SwasthyaEHR (read-only).

Translate flat PostgreSQL rows into nested, standards-compliant FHIR R4 JSON on
the fly. Built by hand (no heavy dependency) so the mapping is explicit and easy
to explain and to pass the official HL7 FHIR validator.

Resources: Patient, Encounter, Observation (lab), Condition (diagnosis),
MedicationRequest (prescription), Observation (vitals), and a Bundle ($everything).
"""

from django.conf import settings

from .constants import Department, LabResultType

PATIENT_ID_SYSTEM = "http://mohp.gov.np/nid"
HOSPITAL_ID_SYSTEM = "https://hospital.swasthya.org.np/ids"

# Every resource leaving this facility is tagged with `_source` so the NUHRS
# portal can attribute records to SwasthyaEHR in the Care Network and per-tab
# source lines (mirrors the other edge services' adapters).
ORG_SOURCE = getattr(settings, "ORG_NAME", "SwasthyaEHR Hospital")

# LOINC codes for the vital-signs panel (http://loinc.org).
VITAL_SIGNS = [
    ("height_cm", "8302-2", "Body height", "cm"),
    ("weight_kg", "29463-7", "Body weight", "kg"),
    ("bmi", "39156-5", "Body mass index (BMI) [Ratio]", "kg/m2"),
    ("systolic_bp", "8480-6", "Systolic blood pressure", "mm[Hg]"),
    ("diastolic_bp", "8462-4", "Diastolic blood pressure", "mm[Hg]"),
    ("pulse", "8867-4", "Heart rate", "/min"),
    ("temperature_c", "8310-5", "Body temperature", "Cel"),
    ("spo2", "59408-5", "Oxygen saturation [SaO2]", "%"),
]


def patient_to_fhir(patient):
    """core.Patient -> FHIR R4 `Patient`."""
    resource = {
        "resourceType": "Patient",
        "id": str(patient.id),
        "active": True,
        "_source": ORG_SOURCE,
        "identifier": [
            {
                "use": "official",
                "system": PATIENT_ID_SYSTEM,
                "value": patient.national_id,
            },
            {
                "use": "secondary",
                "system": HOSPITAL_ID_SYSTEM,
                "value": patient.hospital_identifier,
            },
        ],
        "name": [
            {
                "use": "official",
                "family": patient.last_name,
                "given": [patient.first_name],
                "text": f"{patient.first_name} {patient.last_name}",
            }
        ],
        "telecom": [
            {"system": "phone", "value": patient.phone_number, "use": "mobile"}
        ],
        "gender": (patient.gender or "unknown").lower(),
    }
    if patient.date_of_birth:
        resource["birthDate"] = patient.date_of_birth.isoformat()
    if patient.address:
        resource["address"] = [{"text": patient.address}]
    return resource


def encounter_to_fhir(encounter):
    """core.Encounter -> FHIR R4 `Encounter`."""
    status_map = {
        "REGISTERED": "planned",
        "VITALS_DONE": "arrived",
        "WITH_DOCTOR": "in-progress",
        "LAB_PENDING": "in-progress",
        "LAB_DONE": "in-progress",
        "CLOSED": "finished",
    }
    dept_display = dict(Department.CHOICES).get(
        encounter.department, encounter.department
    )
    return {
        "resourceType": "Encounter",
        "id": str(encounter.id),
        "status": status_map.get(encounter.status, "unknown"),
        "_source": ORG_SOURCE,
        "class": {
            "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
            "code": "AMB",
            "display": "ambulatory",
        },
        "serviceProvider": {"display": ORG_SOURCE},
        "serviceType": {
            "coding": [
                {
                    "system": HOSPITAL_ID_SYSTEM + "/departments",
                    "code": encounter.department,
                    "display": dept_display,
                }
            ],
            "text": dept_display,
        },
        "subject": {"reference": f"Patient/{encounter.patient_id}"},
        "period": {"start": encounter.created_at.isoformat()},
    }


def observation_to_fhir(result):
    """core.LabResult -> FHIR R4 `Observation`."""
    resource = {
        "resourceType": "Observation",
        "id": str(result.id),
        "status": "final",
        "_source": ORG_SOURCE,
        "category": [
            {
                "coding": [
                    {
                        "system": (
                            "http://terminology.hl7.org/CodeSystem/"
                            "observation-category"
                        ),
                        "code": "laboratory",
                        "display": "Laboratory",
                    }
                ]
            }
        ],
        "code": {
            "coding": [],
            "text": result.test_name,
        },
        "subject": {"reference": f"Patient/{result.patient_id}"},
        "effectiveDateTime": result.created_at.isoformat(),
    }
    if result.loinc_code:
        resource["code"]["coding"].append(
            {
                "system": "http://loinc.org",
                "code": result.loinc_code,
                "display": result.test_name,
            }
        )

    if result.result_type == LabResultType.QUANTITATIVE and result.result_value is not None:
        resource["valueQuantity"] = {
            "value": float(result.result_value),
            "unit": result.result_unit,
            "system": "http://unitsofmeasure.org",
            "code": result.result_unit,
        }
        if result.reference_low is not None or result.reference_high is not None:
            ref = {}
            if result.reference_low is not None:
                ref["low"] = {
                    "value": float(result.reference_low),
                    "unit": result.result_unit,
                }
            if result.reference_high is not None:
                ref["high"] = {
                    "value": float(result.reference_high),
                    "unit": result.result_unit,
                }
            resource["referenceRange"] = [ref]
        if result.flag:
            interp = {"LOW": ("L", "Low"), "HIGH": ("H", "High"), "NORMAL": ("N", "Normal")}
            code, display = interp.get(result.flag, ("N", "Normal"))
            resource["interpretation"] = [
                {
                    "coding": [
                        {
                            "system": (
                                "http://terminology.hl7.org/CodeSystem/"
                                "v3-ObservationInterpretation"
                            ),
                            "code": code,
                            "display": display,
                        }
                    ]
                }
            ]
    else:
        resource["valueString"] = result.report_text
    return resource


def vitals_to_fhir(vitals):
    """core.Vitals -> a list of FHIR R4 `Observation` (one per recorded sign).

    A Vitals row is a panel, so each non-null measurement becomes its own
    LOINC-coded Observation. Component ids are derived from the row UUID
    ("<uuid>-<loinc>") so they stay stable across re-serialization.
    """
    resources = []
    for field, loinc, display, unit in VITAL_SIGNS:
        value = getattr(vitals, field)
        if value is None:
            continue
        resources.append(
            {
                "resourceType": "Observation",
                "id": f"{vitals.id}-{loinc}",
                "status": "final",
                "_source": ORG_SOURCE,
                "category": [
                    {
                        "coding": [
                            {
                                "system": (
                                    "http://terminology.hl7.org/CodeSystem/"
                                    "observation-category"
                                ),
                                "code": "vital-signs",
                                "display": "Vital Signs",
                            }
                        ]
                    }
                ],
                "code": {
                    "coding": [
                        {
                            "system": "http://loinc.org",
                            "code": loinc,
                            "display": display,
                        }
                    ],
                    "text": display,
                },
                "subject": {"reference": f"Patient/{vitals.encounter.patient_id}"},
                "effectiveDateTime": vitals.created_at.isoformat(),
                "valueQuantity": {
                    "value": float(value),
                    "unit": unit,
                    "system": "http://unitsofmeasure.org",
                    "code": unit,
                },
            }
        )
    return resources


def condition_to_fhir(diagnosis):
    """core.Diagnosis -> FHIR R4 `Condition`."""
    clinical = "active" if diagnosis.clinical_status == "ACTIVE" else "resolved"
    resource = {
        "resourceType": "Condition",
        "id": str(diagnosis.id),
        "_source": ORG_SOURCE,
        "clinicalStatus": {
            "coding": [
                {
                    "system": (
                        "http://terminology.hl7.org/CodeSystem/condition-clinical"
                    ),
                    "code": clinical,
                }
            ]
        },
        "code": {
            "coding": [
                {
                    "system": "http://hl7.org/fhir/sid/icd-10",
                    "code": diagnosis.icd10_code,
                    "display": diagnosis.disease_name,
                }
            ],
            "text": diagnosis.disease_name,
        },
        "subject": {"reference": f"Patient/{diagnosis.patient_id}"},
        "recordedDate": diagnosis.created_at.isoformat(),
    }
    if diagnosis.onset_date:
        resource["onsetDateTime"] = diagnosis.onset_date.isoformat()
    return resource


def medicationrequest_to_fhir(prescription):
    """core.Prescription -> FHIR R4 `MedicationRequest`."""
    status = "active" if prescription.status == "ACTIVE" else "completed"
    return {
        "resourceType": "MedicationRequest",
        "id": str(prescription.id),
        "status": status,
        "_source": ORG_SOURCE,
        "intent": "order",
        "medicationCodeableConcept": {"text": prescription.medication_name},
        "subject": {"reference": f"Patient/{prescription.patient_id}"},
        "authoredOn": prescription.created_at.isoformat(),
        "dosageInstruction": [{"text": prescription.dosage_instruction}],
    }


def diagnosticreport_to_fhir(report):
    """core.LabReport -> FHIR R4 `DiagnosticReport`.

    The portal groups lab results under their report (groupLabReports resolves
    result[].reference -> top-level Observations), so every confirmed report is
    emitted with references to its analyte Observations.
    """
    order = report.lab_order
    test_name = (order.test_name or order.test_code or "Laboratory test").strip()
    status = "final" if report.status == "CONFIRMED" else "preliminary"
    coding = []
    if order.loinc_code:
        coding.append(
            {
                "system": "http://loinc.org",
                "code": order.loinc_code,
                "display": test_name,
            }
        )
    return {
        "resourceType": "DiagnosticReport",
        "id": str(report.id),
        "status": status,
        "_source": ORG_SOURCE,
        "category": [
            {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/v2-0074",
                        "code": "LAB",
                        "display": "Laboratory",
                    }
                ]
            }
        ],
        "code": {"coding": coding, "text": test_name},
        "subject": {"reference": f"Patient/{report.patient_id}"},
        "effectiveDateTime": report.created_at.isoformat(),
        "result": [
            {"reference": f"Observation/{r.id}", "display": r.test_name or r.test_code}
            for r in report.results.all()
        ],
    }


def build_everything_bundle(
    patient, encounters, results, diagnoses, prescriptions, base_url
):
    """FHIR `Bundle` (type=collection): patient + all related resources."""
    base = base_url.rstrip("/")
    fhir_base = f"{base}/api/fhir/v1"

    def entry(kind, rid, resource):
        return {"fullUrl": f"{fhir_base}/{kind}/{rid}/", "resource": resource}

    entries = [entry("Patient", patient.id, patient_to_fhir(patient))]
    for e in encounters:
        entries.append(entry("Encounter", e.id, encounter_to_fhir(e)))
    for r in results:
        entries.append(entry("Observation", r.id, observation_to_fhir(r)))
    for d in diagnoses:
        entries.append(entry("Condition", d.id, condition_to_fhir(d)))
    for p in prescriptions:
        entries.append(
            entry("MedicationRequest", p.id, medicationrequest_to_fhir(p))
        )

    return {
        "resourceType": "Bundle",
        "type": "collection",
        "total": len(entries),
        "entry": entries,
    }
