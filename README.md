# Vigia

Auditoría de seguridad web automatizada, orientada a PYMES. Escanea un sitio en modo
caja negra (SSL/TLS, headers, cookies, inyecciones, control de acceso, fingerprinting
de tecnologías, subdominios, etc.), genera hallazgos con severidad y produce reportes
(PDF/Excel) y alertas por correo.

## Arquitectura

```
backend/    Django + DRF (API, motor de escaneo, reportes, notificaciones)
frontend/   React + Vite + Tailwind (dashboard, panel admin)
```

### Backend (`backend/`)

| App | Responsabilidad |
|---|---|
| `accounts` | Usuarios, organizaciones, roles, invitaciones, pagos (Stripe) |
| `urls_manager` | URLs/sitios registrados por cada organización |
| `scanner` | Motor de escaneo y catálogo de hallazgos |
| `reports` | Generación de reportes PDF/Excel (ReportLab/WeasyPrint/openpyxl) + resumen ejecutivo con IA (Gemini) |
| `notifications` | Emails transaccionales (Resend): reportes periódicos, alertas de severidad alta |
| `administration` | Panel de superadministrador (métricas, gestión de usuarios/orgs) |
| `audit_log` | Registro de auditoría de requests a la API (evidencia, quién hizo qué) |
| `auditoria` | Proyecto Django raíz (settings, urls, celery) |

**Auth**: Clerk (JWT) — el backend valida el token contra el JWKS de Clerk, no gestiona
contraseñas.

**Roles** (`accounts.User.role`):
- `user` — miembro normal de una organización.
- `org_admin` — puede invitar/revocar miembros de su propia organización. El primer
  usuario que crea una organización se promueve automáticamente a este rol.
- `admin` — superadministrador de la plataforma (todas las orgs, panel `/admin`).

**Async**: Celery + Redis para escaneos en segundo plano y el reporte periódico
programado (`CELERY_BEAT_SCHEDULE`).

### Frontend (`frontend/`)

React 18 + Vite + Tailwind + shadcn/ui. Autenticación vía `@clerk/clerk-react`.
Páginas clave: `Dashboard`, `URLs`, `ScanHistory`/`Report`, `Settings` (equipo e
invitaciones), `admin/AdminDashboard` (panel superadmin).

## Requisitos

- Python 3.12
- Node 18+
- PostgreSQL
- Redis (para Celery)

## Setup

### Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
```

Crear `backend/.env`:

```env
# Django
SECRET_KEY=
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Base de datos (PostgreSQL)
DB_NAME=auditoria_db
DB_USER=postgres
DB_PASSWORD=
DB_HOST=localhost
DB_PORT=5432

# Clerk (https://clerk.com)
CLERK_SECRET_KEY=
CLERK_PUBLISHABLE_KEY=
CLERK_JWKS_URL=
CLERK_ISSUER=

# Google Gemini (resumen ejecutivo con IA)
GEMINI_API_KEY=

# Resend (envío de emails)
RESEND_API_KEY=
RESEND_FROM_EMAIL=Vigia <noreply@tudominio.com>

# Redis / Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Frontend (CORS)
FRONTEND_URL=http://localhost:5173

# Stripe (pagos)
STRIPE_SECRET_KEY=
STRIPE_WEBHOOK_SECRET=
```

```bash
python manage.py migrate
python manage.py runserver
```

Worker + scheduler de Celery (en terminales aparte, requieren Redis corriendo):

```bash
celery -A auditoria worker -l info --pool=solo   # Windows
celery -A auditoria beat -l info
```

### Frontend

```bash
cd frontend
npm install
```

Crear `frontend/.env`:

```env
VITE_CLERK_PUBLISHABLE_KEY=
VITE_STRIPE_PUBLISHABLE_KEY=
```

```bash
npm run dev
```

## Tests

```bash
cd backend
python manage.py test
```

## Notas conocidas

- Sin CI/CD configurado; validar tests y build manualmente antes de cada release.
