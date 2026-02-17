# PaginaAngularDjango

Plataforma fullstack para analisis de mercados Latam con backend Django/DRF + JWT y frontend Angular (standalone).

## Arquitectura
- `backend/`: API REST, auth JWT, roles por grupos, sync de paises/indicadores, riesgo, alertas, portafolios.
- `frontend/`: SPA Angular con guard por autenticacion y roles, vistas de dashboard, paises, portafolios, alertas y sync admin.
- DB: SQLite (desarrollo), con migraciones Django.

## Diagrama ER (resumen)
```text
User ---< Portafolio ---< Posicion >--- Pais ---< IndicadorEconomico
  |            |                           |
  |            |                           +---< TipoCambio
  |            +---< LogActividad
  +---< Alerta >--- Pais

Pais ---< IndiceRiesgo
```

## Stack tecnico
- Backend: Django 6, Django REST Framework, SimpleJWT, corsheaders.
- Frontend: Angular 21, RxJS, standalone components.
- Infra local: Docker Compose opcional.

## Variables de entorno
Copia `.env.example` a `.env` y ajusta valores.

## Ejecucion local (sin Docker)
### Backend
1. `cd backend`
2. `python -m venv .venv`
3. `./.venv/Scripts/python -m pip install -r requirements.txt`
4. `./.venv/Scripts/python manage.py migrate`
5. `./.venv/Scripts/python manage.py runserver 127.0.0.1:8000`

### Frontend
1. `cd frontend`
2. `npm install`
3. `npm start`

Frontend: `http://127.0.0.1:4200`
Backend API: `http://127.0.0.1:8000/api`

## Ejecucion con Docker
1. Crear `.env` basado en `.env.example`
2. `docker compose up --build`

## Endpoints principales
### Auth
- `POST /api/auth/register/`
- `POST /api/auth/login/`
- `POST /api/auth/refresh/`
- `GET /api/auth/me/`
- `PUT /api/auth/me/`

### Paises e indicadores
- `GET /api/paises/`
- `GET /api/paises/{codigo_iso}/`
- `GET /api/paises/{codigo_iso}/indicadores/`
- `GET /api/paises/{codigo_iso}/tipo-cambio/`
- `POST /api/sync/paises/` (ADMIN)
- `POST /api/paises/sync-indicadores/` (ADMIN)

### Portafolios
- `GET /api/portafolios/`
- `POST /api/portafolios/`
- `GET /api/portafolios/{id}/`
- `PUT /api/portafolios/{id}/`
- `DELETE /api/portafolios/{id}/` (soft delete)
- `POST /api/portafolios/{id}/posiciones/`
- `PUT /api/portafolios/{id}/posiciones/{posicion_id}/`
- `DELETE /api/portafolios/{id}/posiciones/{posicion_id}/` (cierre)
- `GET /api/portafolios/{id}/resumen/`
- `GET /api/portafolios/{id}/export/pdf/`

### Riesgo
- `GET /api/riesgo/`
- `GET /api/riesgo/{codigo_iso}/`
- `GET /api/riesgo/{codigo_iso}/historico/`
- `POST /api/riesgo/calcular/` (ADMIN)

### Alertas
- `GET /api/alertas/`
- `PUT /api/alertas/{id}/leer/`
- `PUT /api/alertas/leer-todas/`
- `GET /api/alertas/resumen/`

### Dashboard
- `GET /api/dashboard/resumen/`

## Manejo de errores y logs
- Middleware `api.middleware.RequestLogMiddleware`: log de metodo/path/usuario/duracion/status.
- DRF `api.exception_handler.custom_exception_handler`: payload uniforme para errores.

## Comandos de tareas
- `python manage.py sync_indicadores`
- `python manage.py recalcular_riesgo`

## Pruebas rapidas sugeridas
- Backend: `python manage.py check`
- Frontend: `npx tsc --noEmit`

## Usuarios de prueba
- `viewer1` (VIEWER)
- `analista1` (ANALISTA)
- `user` (ADMIN/superuser)

No se publican contrasenas reales en este repositorio.

## Estado de despliegue
- Base local lista para despliegue.
- Pendiente publicar URLs finales (frontend/backend) en proveedor cloud.
