# Use Python 3.11 slim image for smaller size
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY webapp/requirements.txt ./webapp/
COPY requirements-prod.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements-prod.txt
RUN pip install --no-cache-dir -r webapp/requirements.txt

# Copy application code and data
COPY data/ ./data/
COPY job_transition_model.json ./
COPY employee_transition_model.json ./
COPY webapp/ ./webapp/

# Create a non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8080

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/api/stats').read()"

# Run the application with gunicorn
CMD exec gunicorn --bind :$PORT --workers 2 --threads 4 --timeout 60 --chdir webapp app:app
