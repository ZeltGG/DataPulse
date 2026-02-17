# PaginaAngularDjango

Monorepo de prueba tecnica con backend Django + DRF + JWT y frontend Angular standalone.

## Backend
1. `cd backend`
2. `python -m venv .venv`
3. `./.venv/Scripts/python -m pip install -r requirements.txt`
4. `./.venv/Scripts/python manage.py migrate`
5. `./.venv/Scripts/python manage.py runserver 127.0.0.1:8000`

API base: `http://127.0.0.1:8000/api`

## Frontend
1. `cd frontend`
2. `npm install`
3. `npm start`

Frontend: `http://127.0.0.1:4200`

## Endpoints principales
- `POST /api/auth/login/`
- `POST /api/auth/refresh/`
- `GET /api/auth/me/`
- `POST /api/sync/paises/` (solo ADMIN)
- `GET /api/paises/`
- `GET/POST/DELETE /api/portafolios/` (+ acciones nested de posiciones)

## Usuarios de prueba
- `viewer1` (rol `VIEWER`)
- `analista1` (rol `ANALISTA`)
- `user` (rol `ADMIN`, superuser)

No se incluyen contrasenas reales en este repositorio.
