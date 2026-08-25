"""National Platform API views."""
import secrets
from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from rest_framework import serializers, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie

from . import services
from .permissions import IsExchangeUser, IsMinistryOrSuperAdmin
from .jwt_cookies import (
    REFRESH_COOKIE,
    clear_auth_cookies,
    enforce_csrf,
    set_auth_cookies,
)
from .models import (
    Announcement,
    AuditLog,
    Organization,
    PatientIdentity,
    RecordIndex,
    SSOTicket,
    User,
)
from .validators import (
    is_valid_nid,
    normalize_nid,
    validate_password_policy,
    validate_phone,
)


from .serializers import (
    AnnouncementSerializer,
    AuditLogSerializer,
    OrganizationRegisterSerializer,
    OrganizationSerializer,
    PatientIdentitySerializer,
    RecordIndexSerializer,
    StaffSerializer,
    UserProfileSerializer,
)


def client_ip(request):
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    return xff.split(",")[0] if xff else request.META.get("REMOTE_ADDR")


def issue_tokens(user):
    refresh = RefreshToken.for_user(user)
    return {"access": str(refresh.access_token), "refresh": str(refresh)}


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------
class LoginView(APIView):
    permission_classes = [AllowAny]

    @method_decorator(ensure_csrf_cookie)
    def post(self, request):
        password = request.data.get("password") or ""

        # New scope-based login (Staff / Patient / Official).
        #   STAFF    : {scope, org_code, login_name, password}  role auto-detected
        #   PATIENT  : {scope, username(=NID), password}
        #   OFFICIAL : {scope, username, password}  -> resolves a Super Admin OR
        #              a Ministry account; the returned role picks the dashboard.
        #              ("MINISTRY" is still accepted as a legacy alias.)
        # Falls back to the legacy {username, password} form when no scope given.
        scope = request.data.get("scope")
        if scope:
            user = services.resolve_login_user(
                scope=scope,
                org_code=request.data.get("org_code"),
                login_name=request.data.get("login_name"),
                username=request.data.get("username"),
            )
            if not user or not user.is_active or not user.check_password(password):
                return Response({"detail": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)
        else:
            from django.contrib.auth import authenticate

            username = request.data.get("username")
            user = authenticate(username=username, password=password)
            if not user:
                return Response({"detail": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

        user.last_login = timezone.now()
        user.save(update_fields=["last_login"])
        tokens = issue_tokens(user)
        response = Response({"user": UserProfileSerializer(user).data})
        return set_auth_cookies(response, tokens["access"], tokens["refresh"])


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        new_password = request.data.get("new_password")
        current_password = request.data.get("current_password")
        try:
            validate_password_policy(new_password or "")
        except serializers.ValidationError as exc:
            return Response({"detail": exc.detail[0]}, status=status.HTTP_400_BAD_REQUEST)
        # If current_password is supplied, this is a user-initiated change from a
        # dashboard (not a forced first-login change) — verify it before allowing.
        if current_password and not request.user.check_password(current_password):
            return Response({"detail": "Current password is incorrect"}, status=status.HTTP_400_BAD_REQUEST)
        user = request.user
        user.set_password(new_password)
        user.must_change_password = False
        user.save()
        return Response({"detail": "Password updated"})


class AdminResetPasswordView(APIView):
    """Super admin resets any user's password, issuing a one-time temp password."""
    permission_classes = [IsAuthenticated]

    def post(self, request, user_id):
        if request.user.role != User.Role.SUPER_ADMIN:
            return Response({"detail": "Only super admin"}, status=status.HTTP_403_FORBIDDEN)
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"detail": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        temp_password = services.generate_temp_password()
        user.set_password(temp_password)
        user.must_change_password = True
        user.save()
        return Response({
            "detail": "Password reset",
            "temporary_password": temp_password,
            "username": user.username,
            "login_name": user.login_name or user.username,
        })


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me(request):
    return Response(UserProfileSerializer(request.user).data)


class CsrfView(APIView):
    """Prime the readable csrftoken cookie so the SPA can send X-CSRFToken.

    The SPA calls this once on load (before any write / silent refresh) so the
    double-submit token is in place even on a cold start with an existing
    session cookie.
    """
    permission_classes = [AllowAny]

    @method_decorator(ensure_csrf_cookie)
    def get(self, request):
        return Response({"detail": "ok"})


class LogoutView(APIView):
    """Clear the JWT cookies. CSRF-protected like any other state change."""
    permission_classes = [AllowAny]

    def post(self, request):
        enforce_csrf(request)
        response = Response({"detail": "Logged out."})
        return clear_auth_cookies(response)


class CookieTokenRefreshView(APIView):
    """Mint a fresh access cookie from the httpOnly refresh cookie."""
    permission_classes = [AllowAny]

    def post(self, request):
        enforce_csrf(request)
        raw = request.COOKIES.get(REFRESH_COOKIE)
        if not raw:
            return Response({"detail": "Not authenticated."}, status=status.HTTP_401_UNAUTHORIZED)
        try:
            refresh = RefreshToken(raw)
        except TokenError:
            return Response(
                {"detail": "Session expired. Please sign in again."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        response = Response({"detail": "ok"})
        return set_auth_cookies(response, access=str(refresh.access_token))


# ---------------------------------------------------------------------------
# Single Sign-On (seamless doctor handoff from a trusted facility)
# ---------------------------------------------------------------------------
# A trusted facility (e.g. SwasthyaEHR) that already authenticated its doctor
# exchanges its X-API-Key for a short-lived, single-use ticket tied to that
# doctor's national-platform account. The NUHRS portal then redeems the ticket
# for standard JWT tokens — so the doctor is dropped straight into the National
# Dashboard without re-entering credentials.
SSO_TICKET_TTL_SECONDS = 60


class SSOExchangeView(APIView):
    """
    Step 1 (server-to-server). Facility presents X-API-Key + a doctor_username;
    we mint a single-use ticket (60s TTL) and return it with the portal URL.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        api_key = request.headers.get("X-API-Key")
        try:
            org = Organization.objects.get(
                api_key=api_key, status=Organization.Status.ACTIVE
            )
        except Organization.DoesNotExist:
            return Response({"detail": "Invalid API key"}, status=status.HTTP_401_UNAUTHORIZED)

        doctor_username = (request.data.get("doctor_username") or "").strip()
        if not doctor_username:
            return Response(
                {"detail": "doctor_username is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # The doctor must belong to the facility that owns this API key. If the
        # account doesn't exist yet (fresh national DB), auto-provision it so the
        # integrated handoff "just works" for the demo. It is created disabled
        # for password login (unusable password) — it only ever arrives via SSO.
        user = User.objects.filter(username=doctor_username, organization=org).first()
        if user is None:
            if User.objects.filter(username=doctor_username).exists():
                # Username exists but under a different org — refuse the handoff.
                return Response(
                    {"detail": "Doctor does not belong to this facility."},
                    status=status.HTTP_403_FORBIDDEN,
                )
            login_name = doctor_username.split("-", 1)[-1].lower() or "doctor"
            user = User.objects.create_user(
                username=doctor_username,
                login_name=login_name,
                password=None,  # unusable password — SSO-only account
                full_name=f"{org.organization_name} Doctor",
                email=org.contact_email,
                role=User.Role.DOCTOR,
                organization=org,
                must_change_password=False,
            )
        elif user.role != User.Role.DOCTOR:
            return Response(
                {"detail": "Target account is not a doctor."},
                status=status.HTTP_403_FORBIDDEN,
            )
        if not user.is_active:
            return Response({"detail": "Doctor account is inactive."}, status=status.HTTP_403_FORBIDDEN)

        ticket = secrets.token_urlsafe(32)
        SSOTicket.objects.create(
            ticket=ticket,
            user=user,
            issued_by_org=org,
            expires_at=timezone.now() + timedelta(seconds=SSO_TICKET_TTL_SECONDS),
        )

        portal_url = getattr(settings, "NUHRS_PORTAL_URL", "http://localhost:3000").rstrip("/")
        return Response({
            "ticket": ticket,
            "redirect_url": f"{portal_url}/sso-login",
        })


class SSOVerifyView(APIView):
    """
    Step 2 (browser). The portal posts the ticket; we validate + invalidate it
    (single-use) and return standard JWT tokens for the doctor.
    """
    permission_classes = [AllowAny]

    @method_decorator(ensure_csrf_cookie)
    def post(self, request):
        ticket_value = (request.data.get("ticket") or "").strip()
        if not ticket_value:
            return Response({"detail": "ticket is required."}, status=status.HTTP_400_BAD_REQUEST)

        # Atomically claim the ticket so a concurrent second request can't reuse
        # it. select_for_update + the `used` flag guarantee single-use.
        with transaction.atomic():
            try:
                ticket = (
                    SSOTicket.objects.select_for_update()
                    .select_related("user")
                    .get(ticket=ticket_value)
                )
            except SSOTicket.DoesNotExist:
                return Response(
                    {"detail": "SSO session expired or invalid."},
                    status=status.HTTP_401_UNAUTHORIZED,
                )
            if not ticket.is_valid():
                return Response(
                    {"detail": "SSO session expired or invalid."},
                    status=status.HTTP_401_UNAUTHORIZED,
                )
            ticket.used = True
            ticket.save(update_fields=["used"])
            user = ticket.user

        if not user.is_active:
            return Response({"detail": "Doctor account is inactive."}, status=status.HTTP_403_FORBIDDEN)

        user.last_login = timezone.now()
        user.save(update_fields=["last_login"])
        tokens = issue_tokens(user)
        response = Response({"user": UserProfileSerializer(user).data})
        return set_auth_cookies(response, tokens["access"], tokens["refresh"])


# ---------------------------------------------------------------------------
# Organization registration & approval
# ---------------------------------------------------------------------------

class OrganizationRegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = OrganizationRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        org = serializer.save(status=Organization.Status.PENDING)
        return Response(OrganizationSerializer(org).data, status=status.HTTP_201_CREATED)


class OrganizationListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = Organization.objects.all().order_by("-created_at")
        status_filter = request.query_params.get("status")
        if status_filter:
            qs = qs.filter(status=status_filter)
        return Response(OrganizationSerializer(qs, many=True).data)


class OrganizationApproveView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        if request.user.role != User.Role.SUPER_ADMIN:
            return Response({"detail": "Only super admin can approve"}, status=status.HTTP_403_FORBIDDEN)
        org = Organization.objects.get(pk=pk)
        if org.status == Organization.Status.ACTIVE:
            return Response({"detail": "Already active"}, status=status.HTTP_400_BAD_REQUEST)

        org.organization_code = services.generate_org_code(org.organization_type)
        org.api_key = services.generate_api_key()
        org.status = Organization.Status.ACTIVE
        org.save()

        admin_username = services.generate_admin_username(org.organization_code)
        temp_password = services.generate_temp_password()
        User.objects.create_user(
            username=admin_username,
            login_name="admin",
            password=temp_password,
            full_name=f"{org.organization_name} Admin",
            email=org.contact_email,
            phone=org.contact_phone,
            role=User.Role.ORGANIZATION_ADMIN,
            organization=org,
            must_change_password=True,
        )
        # credentials shown once. The admin signs in with the STAFF scope using
        # this organization_code + login_name "admin".
        return Response({
            "organization_code": org.organization_code,
            "admin_username": admin_username,
            "login_name": "admin",
            "temporary_password": temp_password,
            "api_key": org.api_key,
        })


class OrganizationRejectView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        if request.user.role != User.Role.SUPER_ADMIN:
            return Response({"detail": "Only super admin can reject"}, status=status.HTTP_403_FORBIDDEN)
        org = Organization.objects.get(pk=pk)
        org.status = Organization.Status.REJECTED
        org.save()
        return Response({"detail": "Rejected"})


class OrganizationSuspendView(APIView):
    """Ministry admin suspends an active organization."""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        if request.user.role != User.Role.SUPER_ADMIN:
            return Response({"detail": "Only super admin"}, status=status.HTTP_403_FORBIDDEN)
        try:
            org = Organization.objects.get(pk=pk)
        except Organization.DoesNotExist:
            return Response({"detail": "Organization not found"}, status=status.HTTP_404_NOT_FOUND)
        if org.status != Organization.Status.ACTIVE:
            return Response({"detail": "Only active orgs can be suspended"}, status=status.HTTP_400_BAD_REQUEST)
        org.status = Organization.Status.SUSPENDED
        org.save()
        return Response({"detail": "Organization suspended"})


class OrganizationReactivateView(APIView):
    """Ministry admin reactivates a suspended organization."""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        if request.user.role != User.Role.SUPER_ADMIN:
            return Response({"detail": "Only super admin"}, status=status.HTTP_403_FORBIDDEN)
        try:
            org = Organization.objects.get(pk=pk)
        except Organization.DoesNotExist:
            return Response({"detail": "Organization not found"}, status=status.HTTP_404_NOT_FOUND)
        if org.status != Organization.Status.SUSPENDED:
            return Response({"detail": "Only suspended orgs can be reactivated"}, status=status.HTTP_400_BAD_REQUEST)
        org.status = Organization.Status.ACTIVE
        org.save()
        return Response({"detail": "Organization reactivated"})


class ActiveOrganizationsView(APIView):
    """Public endpoint for the doctor login hospital dropdown."""
    permission_classes = [AllowAny]

    def get(self, request):
        orgs = Organization.objects.filter(status=Organization.Status.ACTIVE).values(
            "id", "organization_code", "organization_name", "organization_type"
        ).order_by("organization_name")
        return Response(list(orgs))


# ---------------------------------------------------------------------------
# Organization admin — staff management
# ---------------------------------------------------------------------------
class StaffView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        org = request.user.organization
        qs = User.objects.filter(organization=org).exclude(role=User.Role.ORGANIZATION_ADMIN)
        return Response(StaffSerializer(qs, many=True).data)

    def post(self, request):
        if request.user.role != User.Role.ORGANIZATION_ADMIN:
            return Response({"detail": "Only org admin"}, status=status.HTTP_403_FORBIDDEN)
        org = request.user.organization
        role = request.data.get("role", User.Role.DOCTOR)
        prefix = "DOC" if role == User.Role.DOCTOR else "TECH"

        # login_name is the short handle the staff member types at login. The
        # admin may supply one; otherwise we generate a sequential default like
        # "doc0001". It must be unique within this organization.
        count = User.objects.filter(organization=org, role=role).count() + 1
        login_name = (request.data.get("login_name") or f"{prefix.lower()}{count:04d}").strip()
        if User.objects.filter(organization=org, login_name__iexact=login_name).exists():
            return Response(
                {"detail": f"Login name '{login_name}' already exists in this organization."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # username stays globally unique (Django auth requirement) but is never
        # typed by the user; compose it from org code + login_name.
        username = f"{org.organization_code}-{login_name}"
        phone = (request.data.get("phone") or "").strip()
        if phone:
            try:
                phone = validate_phone(phone)
            except serializers.ValidationError as exc:
                return Response({"detail": exc.detail[0]}, status=status.HTTP_400_BAD_REQUEST)
        temp_password = services.generate_temp_password()
        user = User.objects.create_user(
            username=username,
            login_name=login_name,
            password=temp_password,
            full_name=request.data.get("full_name", ""),
            email=request.data.get("email", ""),
            phone=phone,
            role=role,
            organization=org,
            must_change_password=True,
        )
        return Response(
            {**StaffSerializer(user).data, "temporary_password": temp_password},
            status=status.HTTP_201_CREATED,
        )


class AllUsersView(APIView):
    """Ministry admin views all users across organizations."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != User.Role.SUPER_ADMIN:
            return Response({"detail": "Only super admin"}, status=status.HTTP_403_FORBIDDEN)

        role_filter = request.query_params.get("role")
        org_filter = request.query_params.get("organization")

        qs = User.objects.all().select_related("organization", "patient_identity")
        if role_filter:
            qs = qs.filter(role=role_filter)
        if org_filter:
            qs = qs.filter(organization__id=org_filter)

        return Response(UserProfileSerializer(qs.order_by("-created_at"), many=True).data)


# ---------------------------------------------------------------------------
# Ministry accounts (Super Admin creates/lists/deletes the restricted role)
# ---------------------------------------------------------------------------
class MinistryUserView(APIView):
    """Super admin creates and lists Ministry accounts.

    A Ministry account is a privileged, organization-less user whose only
    powers are broadcasting announcements and viewing national analytics.
    Only a Super Admin may mint or list them — the gate below rejects Ministry
    users themselves, so a Ministry account cannot create more of its own kind.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != User.Role.SUPER_ADMIN:
            return Response({"detail": "Only super admin"}, status=status.HTTP_403_FORBIDDEN)
        qs = User.objects.filter(role=User.Role.MINISTRY).order_by("-created_at")
        return Response(StaffSerializer(qs, many=True).data)

    def post(self, request):
        if request.user.role != User.Role.SUPER_ADMIN:
            return Response({"detail": "Only super admin"}, status=status.HTTP_403_FORBIDDEN)

        username = (request.data.get("username") or "").strip()
        if not username:
            return Response({"detail": "Username is required."}, status=status.HTTP_400_BAD_REQUEST)
        # username is the globally-unique handle the official types on the
        # Official login tab, so it must not clash with any existing account.
        if User.objects.filter(username__iexact=username).exists():
            return Response(
                {"detail": f"Username '{username}' is already taken."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        temp_password = services.generate_temp_password()
        user = User.objects.create_user(
            username=username,
            login_name=username,
            password=temp_password,
            full_name=request.data.get("full_name", ""),
            email=request.data.get("email", ""),
            phone=request.data.get("phone", ""),
            role=User.Role.MINISTRY,
            organization=None,
            must_change_password=True,
        )
        # Temp password is shown once, mirroring org-admin approval / StaffView.
        return Response(
            {**StaffSerializer(user).data, "temporary_password": temp_password},
            status=status.HTTP_201_CREATED,
        )


class MinistryUserDetailView(APIView):
    """Super admin deletes a Ministry account."""
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        if request.user.role != User.Role.SUPER_ADMIN:
            return Response({"detail": "Only super admin"}, status=status.HTTP_403_FORBIDDEN)
        try:
            user = User.objects.get(pk=pk, role=User.Role.MINISTRY)
        except User.DoesNotExist:
            return Response({"detail": "Ministry account not found"}, status=status.HTTP_404_NOT_FOUND)
        user.delete()
        return Response({"detail": "Deleted"}, status=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# Exchange engine (doctor)
# ---------------------------------------------------------------------------
class PatientLookupView(APIView):
    permission_classes = [IsAuthenticated, IsExchangeUser]

    def get(self, request, nid):
        try:
            patient = PatientIdentity.objects.get(nid=nid)
        except PatientIdentity.DoesNotExist:
            return Response({"detail": "Patient not found"}, status=status.HTTP_404_NOT_FOUND)
        AuditLog.objects.create(
            actor_user=request.user, actor_org=request.user.organization,
            nid=nid, action=AuditLog.Action.SEARCH, ip_address=client_ip(request),
        )
        return Response(PatientIdentitySerializer(patient).data)


class PatientIndexView(APIView):
    permission_classes = [IsAuthenticated, IsExchangeUser]

    def get(self, request, nid):
        qs = RecordIndex.objects.filter(patient__nid=nid).select_related("organization")
        return Response(RecordIndexSerializer(qs, many=True).data)


class PatientFetchView(APIView):
    permission_classes = [IsAuthenticated, IsExchangeUser]

    def post(self, request, nid):
        mode = request.data.get("mode", "ALL")
        engine = services.RoutingEngine(actor_user=request.user, ip_address=client_ip(request))
        if mode == "ONE":
            record_index_id = request.data.get("record_index_id")
            bundle = engine.fetch_one(nid, record_index_id)
        else:
            bundle = engine.fetch_all(nid)
        return Response(bundle)


# ---------------------------------------------------------------------------
# Patient portal
# ---------------------------------------------------------------------------
class PatientActivateView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        nid = normalize_nid(request.data.get("nid"))
        dob = request.data.get("date_of_birth")
        phone = request.data.get("phone")
        password = request.data.get("password")
        if not is_valid_nid(nid):
            return Response(
                {"detail": "National ID must be exactly 10 digits (Nepal NIN)."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            validate_password_policy(password or "")
        except serializers.ValidationError as exc:
            return Response({"detail": exc.detail[0]}, status=status.HTTP_400_BAD_REQUEST)
        # Identity must exist in the national Master Patient Index. It is created
        # when any hospital/lab first indexes a record for this NID (or by the
        # demo bootstrap). If it's missing, the citizen has no records anywhere
        # yet — guide them accordingly instead of a generic failure.
        try:
            patient = PatientIdentity.objects.get(nid=nid)
        except PatientIdentity.DoesNotExist:
            return Response(
                {"detail": "No health record found for this National ID. Visit a "
                           "registered hospital or lab first, then try again."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        # Verify date of birth (required). Phone is verified only if the citizen
        # supplied one AND we have one on file — a small typo in an optional field
        # shouldn't block activation of the correct person.
        if not dob or str(patient.date_of_birth) != str(dob):
            return Response(
                {"detail": "Identity verification failed: date of birth does not match our records."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if phone and patient.phone and phone.strip() != patient.phone:
            return Response(
                {"detail": "Identity verification failed: phone number does not match our records."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if User.objects.filter(username=nid).exists():
            return Response(
                {"detail": "This account is already activated — please sign in instead."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        User.objects.create_user(
            username=nid, password=password, full_name=patient.full_name,
            email=patient.email, phone=patient.phone,
            role=User.Role.PATIENT, patient_identity=patient,
        )
        return Response({"detail": "Account activated"}, status=status.HTTP_201_CREATED)


class PatientRegisterView(APIView):
    """
    Self-registration for citizens with no records in the MPI yet. Creates a
    PatientIdentity and a PATIENT User in one step. Distinct from activation,
    which requires the identity to already exist.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        nid = normalize_nid(request.data.get("nid"))
        full_name = (request.data.get("full_name") or "").strip()
        dob = request.data.get("date_of_birth")
        gender = request.data.get("gender", PatientIdentity.Gender.OTHER)
        phone = (request.data.get("phone") or "").strip()
        email = (request.data.get("email") or "").strip()
        password = request.data.get("password")

        if not is_valid_nid(nid):
            return Response(
                {"detail": "National ID must be exactly 10 digits (Nepal NIN)."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            validate_password_policy(password or "")
        except serializers.ValidationError as exc:
            return Response({"detail": exc.detail[0]}, status=status.HTTP_400_BAD_REQUEST)
        if phone:
            try:
                phone = validate_phone(phone)
            except serializers.ValidationError as exc:
                return Response({"detail": exc.detail[0]}, status=status.HTTP_400_BAD_REQUEST)
        if not full_name or not dob:
            return Response(
                {"detail": "Full name and date of birth are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if PatientIdentity.objects.filter(nid=nid).exists():
            return Response(
                {"detail": "This National ID is already registered. Use the "
                           "Sign In tab if you have existing health records."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if User.objects.filter(username=nid).exists():
            return Response(
                {"detail": "This account already exists — please sign in instead."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        patient = PatientIdentity.objects.create(
            nid=nid, full_name=full_name, date_of_birth=dob,
            gender=gender, phone=phone, email=email,
        )
        User.objects.create_user(
            username=nid, password=password, full_name=full_name,
            email=email, phone=phone,
            role=User.Role.PATIENT, patient_identity=patient,
        )
        return Response({"detail": "Registration successful"}, status=status.HTTP_201_CREATED)


class PatientMyRecordsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != User.Role.PATIENT or not request.user.patient_identity:
            return Response({"detail": "Not a patient account"}, status=status.HTTP_403_FORBIDDEN)
        nid = request.user.patient_identity.nid
        qs = RecordIndex.objects.filter(patient__nid=nid).select_related("organization")
        return Response({
            "patient": PatientIdentitySerializer(request.user.patient_identity).data,
            "records": RecordIndexSerializer(qs, many=True).data,
        })


class PatientMyBundleView(APIView):
    """
    Self-scoped aggregated FHIR fetch for the logged-in patient. Unlike
    PatientFetchView (doctor-facing, arbitrary NID), the NID here is derived
    ONLY from the authenticated patient's own identity — never from the request
    — so a patient can never fetch another patient's record.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != User.Role.PATIENT or not request.user.patient_identity:
            return Response({"detail": "Not a patient account"}, status=status.HTTP_403_FORBIDDEN)
        nid = request.user.patient_identity.nid
        engine = services.RoutingEngine(actor_user=request.user, ip_address=client_ip(request))
        bundle = engine.fetch_all(nid)
        return Response({
            "patient": PatientIdentitySerializer(request.user.patient_identity).data,
            "bundle": bundle,
        })


# ---------------------------------------------------------------------------
# National health announcements (Ministry authors, everyone reads)
# ---------------------------------------------------------------------------
class AnnouncementListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = Announcement.objects.filter(is_published=True)
        return Response(AnnouncementSerializer(qs, many=True).data)

    def post(self, request):
        # Broadcasting announcements is one of Ministry's two powers, so the
        # gate is widened beyond Super Admin here (and on delete below).
        if request.user.role not in (User.Role.SUPER_ADMIN, User.Role.MINISTRY):
            return Response({"detail": "Only super admin or ministry"}, status=status.HTTP_403_FORBIDDEN)
        serializer = AnnouncementSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(author=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class AnnouncementDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        if request.user.role not in (User.Role.SUPER_ADMIN, User.Role.MINISTRY):
            return Response({"detail": "Only super admin or ministry"}, status=status.HTTP_403_FORBIDDEN)
        try:
            announcement = Announcement.objects.get(pk=pk)
        except Announcement.DoesNotExist:
            return Response({"detail": "Announcement not found"}, status=status.HTTP_404_NOT_FOUND)
        announcement.delete()
        return Response({"detail": "Deleted"}, status=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# Metadata ingest (called by hospitals/labs with X-API-Key)
# ---------------------------------------------------------------------------
class IndexIngestView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        api_key = request.headers.get("X-API-Key")
        try:
            org = Organization.objects.get(api_key=api_key, status=Organization.Status.ACTIVE)
        except Organization.DoesNotExist:
            return Response({"detail": "Invalid API key"}, status=status.HTTP_401_UNAUTHORIZED)

        p = request.data.get("patient", {})
        nid = normalize_nid(request.data.get("nid") or p.get("nid"))
        if not is_valid_nid(nid):
            return Response(
                {"detail": "National ID must be exactly 10 digits (Nepal NIN)."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        patient, _ = PatientIdentity.objects.get_or_create(
            nid=nid,

            defaults={
                "full_name": p.get("full_name", ""),
                "date_of_birth": p.get("date_of_birth"),
                "gender": p.get("gender", PatientIdentity.Gender.OTHER),
                "phone": p.get("phone", ""),
                "email": p.get("email", ""),
            },
        )
        # Upsert on the natural key of a record so re-indexing the same source
        # row (e.g. re-running a seed) updates in place instead of creating a
        # duplicate index entry — otherwise the same reading appears many times
        # and clutters the trend chart / timeline.
        record, created = RecordIndex.objects.update_or_create(
            organization=org,
            resource_type=request.data.get("resource_type"),
            local_record_id=request.data.get("local_record_id"),
            defaults={
                "patient": patient,
                "service_date": request.data.get("service_date"),
                "summary": request.data.get("summary", ""),
            },
        )
        code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return Response({"detail": "indexed", "record_index_id": record.id}, status=code)



# ---------------------------------------------------------------------------
# Audit & analytics
# ---------------------------------------------------------------------------
class AuditLogView(APIView):
    permission_classes = [IsAuthenticated, IsMinistryOrSuperAdmin]

    def get(self, request):
        qs = AuditLog.objects.all().select_related("actor_user", "actor_org")
        if request.query_params.get("nid"):
            qs = qs.filter(nid=request.query_params["nid"])
        if request.query_params.get("action"):
            qs = qs.filter(action=request.query_params["action"])
        return Response(AuditLogSerializer(qs[:200], many=True).data)


class AnalyticsSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # National analytics is shared by the two privileged roles only —
        # doctors/patients/org-admins must not read aggregate national stats.
        if request.user.role not in (User.Role.SUPER_ADMIN, User.Role.MINISTRY):
            return Response({"detail": "Only super admin or ministry"}, status=status.HTTP_403_FORBIDDEN)
        from django.db.models import Count

        top_conditions = list(
            RecordIndex.objects.filter(resource_type=RecordIndex.ResourceType.CONDITION)
            .values("summary")
            .annotate(count=Count("id"))
            .order_by("-count")[:10]
        )
        by_province = list(
            RecordIndex.objects.values("organization__province")
            .annotate(count=Count("id"))
            .order_by("-count")
        )
        return Response({
            "total_records_indexed": RecordIndex.objects.count(),
            "total_patients": PatientIdentity.objects.count(),
            "total_organizations": Organization.objects.filter(status=Organization.Status.ACTIVE).count(),
            "total_exchanges": AuditLog.objects.filter(
                action__in=[AuditLog.Action.FETCH_ALL, AuditLog.Action.FETCH_ONE]
            ).count(),
            "top_conditions": top_conditions,
            "records_by_province": by_province,
        })
