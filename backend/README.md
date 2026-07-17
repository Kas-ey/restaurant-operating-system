# ROS Backend

Backend services for the Restaurant Operating System (ROS), implemented with Flask, SQLAlchemy, and Flask-Migrate.

## Prerequisites

- Python 3.14+
- PostgreSQL 14+
- pip

## Dependency Management

- Authoritative backend dependency file: `backend/requirements.txt`
- Do not use the workspace root `requirements.txt` for backend setup.

## Environment Setup

1. Create a virtual environment:
   - Windows:
     - `python -m venv .venv`
     - `.venv\Scripts\activate`
   - macOS/Linux:
     - `python -m venv .venv`
     - `source .venv/bin/activate`
2. Install dependencies:
   - `pip install -r requirements.txt`
3. Create local environment file from the template:
   - Windows: `copy .env.example .env`
   - macOS/Linux: `cp .env.example .env`
4. Configure `DATABASE_URL` in `.env` using this format:
   - `postgresql://username:password@localhost:5432/database_name`

Required environment variables:

- `DATABASE_URL`
- `SECRET_KEY`
- `LOG_LEVEL` (default: `INFO`)

## Database Initialization

From `backend/`:

1. Apply migrations:
   - `flask --app ros:create_app db upgrade`
2. (Optional) Check current revision:
   - `flask --app ros:create_app db current`

## Running the Backend

From `backend/`:

- `python run.py`

Default health endpoint:

- `GET /api/v1/health`

## Development Workflow

1. Pull latest changes.
2. Activate virtual environment.
3. Install/update dependencies from `backend/requirements.txt`.
4. Ensure `.env` is configured.
5. Run `flask --app ros:create_app db upgrade`.
6. Start server with `python run.py`.

## Troubleshooting

- Startup fails with `DATABASE_URL environment variable is required`:
  - Ensure `.env` exists in `backend/` and has a non-empty `DATABASE_URL`.
- Startup fails with database URL parsing errors (for example invalid port):
  - Verify `DATABASE_URL` follows `postgresql://username:password@localhost:5432/database_name`.
- Migration command fails to find app:
  - Run commands from `backend/` and use `--app ros:create_app`.
- Import errors after dependency changes:
  - Re-activate `.venv` and run `pip install -r requirements.txt` again.
