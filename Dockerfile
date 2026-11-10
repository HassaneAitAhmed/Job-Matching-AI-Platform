# ---- 1. Build the React frontend ----
FROM node:22-alpine AS frontend
WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# ---- 2. Python app serving the API and the built frontend ----
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn==23.0.0

COPY matching/ matching/
COPY webapp/ webapp/
COPY data/ data/
COPY --from=frontend /frontend/dist frontend/dist

RUN useradd --create-home appuser
USER appuser

# Hosts such as Render inject PORT; default to 8000 for `docker run`.
ENV PORT=8000
EXPOSE 8000
# One worker process holds the data in memory (~200 MB); scale with threads.
# --preload loads the data before accepting traffic, so health checks wait for it.
CMD ["sh", "-c", "exec gunicorn --bind 0.0.0.0:${PORT} --workers 1 --threads 4 --timeout 120 --preload 'webapp.app:create_app()'"]
