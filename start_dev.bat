@echo off
setlocal enabledelayedexpansion

echo ========================================================
echo Iniciando Entorno de Desarrollo de ScanOps...
echo ========================================================

echo [1/2] Obteniendo Stripe Webhook Secret y actualizando .env...
for /f "delims=" %%i in ('.\stripe.exe listen --print-secret') do set "WHSEC=%%i"

if "!WHSEC!"=="" (
    echo [ADVERTENCIA] No se pudo obtener el secreto. Verifica tu conexion de stripe CLI.
) else (
    findstr /v "STRIPE_WEBHOOK_SECRET=" backend\.env > backend\.env.tmp
    echo STRIPE_WEBHOOK_SECRET=!WHSEC!>> backend\.env.tmp
    move /Y backend\.env.tmp backend\.env > nul
    echo Exito! Se actualizo el backend/.env automaticamente con el secreto.
)

echo [2/2] Abriendo servidores en Windows Terminal...
wt -d backend cmd /k "title Backend (Django) && python manage.py runserver" ; new-tab -d frontend cmd /k "title Frontend (Vite) && npm run dev" ; new-tab -d . cmd /k "title Stripe Webhooks && .\stripe.exe listen --forward-to localhost:8000/api/auth/payments/webhook/"

echo ========================================================
echo ¡Todo ha sido lanzado correctamente en una nueva ventana!
echo ========================================================
pause
