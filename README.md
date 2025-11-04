### Django API (Backend)

Backend for the ELD Trip Planner. Built with Django + Django REST Framework. Defaults to SQLite for local/dev.

#### Prerequisites

- Python 3.10+

#### Setup

```bash
cd api
python3 -m venv ../.venv
source ../.venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

Optional env file `api/.env`:

```env
DJANGO_SECRET_KEY=change-me
DJANGO_DEBUG=true
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOW_ALL=true
# DATABASE_URL (unset ⇒ SQLite at api/db.sqlite3)
# DATABASE_URL=postgresql://user:pass@host:port/db
```

Env is auto‑loaded (python‑dotenv). If `DATABASE_URL` is unset, SQLite is used.

#### Database and sample data

```bash
../.venv/bin/python manage.py migrate
../.venv/bin/python manage.py seed_sample
```

This creates tables and inserts a sample Trip/LogDay so the UI can render an ELD sheet.

#### Run locally

```bash
../.venv/bin/python manage.py runserver 8000
```

Open:

- API health: http://localhost:8000/health
- API docs: http://localhost:8000/api/docs/

#### Key files

- `api/api/settings.py` — env, DRF, CORS, database
- `trips/` — models, serializers, views, routes under `/api/v1/`

#### Endpoints

- POST `/api/v1/trips/` — create trip and return plan/logs (sample)
- GET `/api/v1/trips/` — list trips

#### Common commands

```bash
../.venv/bin/python manage.py makemigrations
../.venv/bin/python manage.py migrate
../.venv/bin/python manage.py runserver 8000
```

#### Troubleshooting

- Using SQLite by default. If you previously set `DATABASE_URL` in your shell, unset it: `unset DATABASE_URL`.
- For hosted frontends, set `CORS_ALLOWED_ORIGINS` (or keep `CORS_ALLOW_ALL=true` in dev).

#### Docker / Deploy (optional)

- Local/dev works without Docker using SQLite.
- To deploy on Render, see repo root `README.md` (Render section) and use `render.yaml`.

For full repo setup and the frontend, see the root `README.md`.
