"""
HL7 FHIR R4 serializers for SwasthyaEHR (read-only).

Translate flat PostgreSQL rows into nested, standards-compliant FHIR R4 JSON on
the fly. Built by hand (no heavy dependency) so the mapping is explicit and easy
to explain and to pass the official HL7 FHIR validator.

Resources: Patient, Encounter, Observation (lab), Condition (diagnosis),
MedicationRequest (prescription), and a Bundle ($everything).
"""

from .constants import Department, LabResultType

PATIENT_ID_SYSTEM = "http://mohp.gov.np/nid"
HOSPITAL_ID_SYSTEM = "https://hospital.swasthya.org.np/ids"


def patient_to_fhir(patient):
    """core.Patient -> FHIR R4 `Patient`."""
    resource = {
        "resourceType": "Patient",
        "id": str(patient.id),
        "active": True,
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
        "class": {
            "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
            "code": "AMB",
            "display": "ambulatory",
        },
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


def condition_to_fhir(diagnosis):
    """core.Diagnosis -> FHIR R4 `Condition`."""
    clinical = "active" if diagnosis.clinical_status == "ACTIVE" else "resolved"
    resource = {
        "resourceType": "Condition",
        "id": str(diagnosis.id),
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
        "intent": "order",
        "medicationCodeableConcept": {"text": prescription.medication_name},
        "subject": {"reference": f"Patient/{prescription.patient_id}"},
        "authoredOn": prescription.created_at.isoformat(),
        "dosageInstruction": [{"text": prescription.dosage_instruction}],
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
