# ROS Backend

## Environment setup

1. Create a virtual environment:
   `python -m venv .venv`
2. Activate it:
   - Windows: `.venv\Scripts\activate`
   - macOS/Linux: `source .venv/bin/activate`
3. Install dependencies:
   `pip install -r requirements.txt`
4. Create a local environment file:
   `copy .env.example .env` (Windows) or `cp .env.example .env` (macOS/Linux)
5. Configure PostgreSQL and set `DATABASE_URL` in `.env`.
6. Start the application:
   `python run.py`
