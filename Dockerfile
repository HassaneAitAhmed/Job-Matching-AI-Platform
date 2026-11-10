FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn==23.0.0

COPY matching/ matching/
COPY webapp/ webapp/
COPY data/ data/

RUN useradd --create-home appuser
USER appuser

EXPOSE 8000
# One worker process holds the data in memory (~150 MB); scale with threads.
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "1", "--threads", "4", "--timeout", "60", "webapp.app:create_app()"]
