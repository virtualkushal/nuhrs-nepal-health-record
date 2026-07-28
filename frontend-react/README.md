# NUHRS Frontend (React + Vite)

Modular React single-page app for the Nepal Unified Health Record System. It
replaces the original vanilla-JS app in `../frontend` with a component-based,
route-driven architecture while talking to the same National Platform API.

## Structure

```
src/
  lib/api.js               # fetch wrapper + JWT/session helpers
  context/
    AuthContext.jsx        # user session state (login/logout/role)
    ToastContext.jsx       # transient notifications
  components/
    AppShell.jsx           # top bar for authenticated screens
    ui.jsx                 # Card, Field, Table, Badge, Stat primitives
    ResourceCard.jsx       # FHIR resource renderer
  pages/
    Landing.jsx            # public home page (Stitch design) + login
    RegisterOrg.jsx        # org self-registration (+ shared AuthLayout)
    ActivatePatient.jsx    # patient self-activation
    ChangePassword.jsx     # forced temp-password change
    Dashboard.jsx          # role dispatcher (wrapped in AppShell)
    dashboards/
      SuperAdmin.jsx       # orgs / analytics / audit tabs
      OrgAdmin.jsx         # staff management
      Exchange.jsx         # doctor/lab record exchange
      PatientPortal.jsx    # patient's own records
  App.jsx                  # routes
  main.jsx                 # providers + router bootstrap
```

## Local development

```bash
npm install
npm run dev          # http://localhost:5173
```

The API base defaults to `http://localhost:8000`. Override without rebuilding:

```js
localStorage.setItem("nuhrs_api", "http://localhost:8000");
```

Or at build time via the `VITE_PLATFORM_API` env/arg.

## Production / Docker

Built and served by nginx (see `Dockerfile`). Run the full stack from the repo
root:

```bash
docker compose up --build frontend
```

Served on http://localhost:3000.

Design tokens (colors, fonts, spacing) live in `tailwind.config.js` and were
derived from the Stitch "NUHRS Health Portal" project.
