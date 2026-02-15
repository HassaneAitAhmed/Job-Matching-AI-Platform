# Deployment Guide for Job Matching AI Platform

This guide provides multiple options for hosting and deploying the Job Matching AI Platform web application.

## Table of Contents

1. [Quick Start with Docker](#quick-start-with-docker)
2. [Deploy to Heroku](#deploy-to-heroku)
3. [Deploy to Railway](#deploy-to-railway)
4. [Deploy to Render](#deploy-to-render)
5. [Deploy to Google Cloud Run](#deploy-to-google-cloud-run)
6. [Deploy to PythonAnywhere](#deploy-to-pythonanywhere)
7. [VPS Deployment](#vps-deployment)
8. [Environment Variables](#environment-variables)

---

## Quick Start with Docker

The easiest way to deploy anywhere is using Docker.

### Prerequisites
- Docker installed on your system
- Docker Compose (optional, but recommended)

### Build and Run

**Using Docker Compose (Recommended):**
```bash
docker-compose up -d
```

The application will be available at `http://localhost:8080`

**Using Docker directly:**
```bash
# Build the image
docker build -t job-matching-ai .

# Run the container
docker run -p 8080:8080 job-matching-ai
```

### Stop the Application
```bash
docker-compose down
```

---

## Deploy to Heroku

Heroku is a popular Platform-as-a-Service (PaaS) that makes deployment simple.

### Prerequisites
- Heroku account (free tier available)
- Heroku CLI installed

### Deployment Steps

1. **Login to Heroku:**
```bash
heroku login
```

2. **Create a new Heroku app:**
```bash
heroku create your-app-name
```

3. **Deploy the application:**
```bash
git push heroku copilot/create-ai-project-website:main
```

Or if you're on main branch:
```bash
git push heroku main
```

4. **Open your application:**
```bash
heroku open
```

### Heroku Configuration

The following files are included for Heroku:
- `Procfile` - Tells Heroku how to run your app
- `runtime.txt` - Specifies Python version
- `requirements.txt` - Lists all dependencies

### Scale Your App
```bash
# Check current dynos
heroku ps

# Scale to 1 web dyno
heroku ps:scale web=1
```

### View Logs
```bash
heroku logs --tail
```

### Estimated Cost
- Free tier: 550-1000 hours/month
- Hobby tier: $7/month for 24/7 uptime

---

## Deploy to Railway

Railway offers modern deployment with automatic SSL and custom domains.

### Prerequisites
- Railway account (sign up at railway.app)
- Railway CLI (optional)

### Deployment Steps

#### Method 1: Using Railway Dashboard (Easiest)

1. Go to [railway.app](https://railway.app)
2. Click **"New Project"** → **"Deploy from GitHub repo"**
3. Connect your GitHub account and select this repository
4. Railway will automatically detect the configuration
5. Click **"Deploy"**
6. Your app will be live in minutes!

#### Method 2: Using Railway CLI

1. **Install Railway CLI:**
```bash
npm i -g @railway/cli
# or
brew install railway
```

2. **Login:**
```bash
railway login
```

3. **Initialize and deploy:**
```bash
railway init
railway up
```

4. **Open your app:**
```bash
railway open
```

### Railway Configuration

Railway automatically detects:
- `Procfile` for build commands
- `requirements.txt` for dependencies
- Port from environment variable

### Estimated Cost
- Free tier: $5 credit/month (limited hours)
- Hobby: $5/month + usage

---

## Deploy to Render

Render provides free web service hosting with automatic deployments.

### Prerequisites
- Render account (sign up at render.com)

### Deployment Steps

1. Go to [render.com](https://render.com)
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repository
4. Configure the service:
   - **Name:** job-matching-ai
   - **Environment:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn --bind :$PORT --workers 2 --threads 4 --timeout 60 --chdir webapp app:app`
5. Click **"Create Web Service"**

### Render Configuration

Create a `render.yaml` file for automated deployment:

```yaml
services:
  - type: web
    name: job-matching-ai
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: gunicorn --bind :$PORT --workers 2 --threads 4 --timeout 60 --chdir webapp app:app
    envVars:
      - key: PYTHON_VERSION
        value: 3.11.7
      - key: FLASK_DEBUG
        value: false
```

### Estimated Cost
- Free tier: Available (with limitations)
- Starter: $7/month

---

## Deploy to Google Cloud Run

Google Cloud Run offers serverless container deployment.

### Prerequisites
- Google Cloud account
- gcloud CLI installed
- Docker installed

### Deployment Steps

1. **Authenticate with Google Cloud:**
```bash
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
```

2. **Build and push Docker image:**
```bash
# Enable required APIs
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com

# Build and push
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/job-matching-ai

# Or using Docker
docker build -t gcr.io/YOUR_PROJECT_ID/job-matching-ai .
docker push gcr.io/YOUR_PROJECT_ID/job-matching-ai
```

3. **Deploy to Cloud Run:**
```bash
gcloud run deploy job-matching-ai \
  --image gcr.io/YOUR_PROJECT_ID/job-matching-ai \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --port 8080 \
  --memory 1Gi
```

4. **Access your application:**
The command will output your application URL.

### Estimated Cost
- Free tier: 2 million requests/month
- Pay-as-you-go after that

---

## Deploy to PythonAnywhere

PythonAnywhere is great for Python web apps and offers a free tier.

### Prerequisites
- PythonAnywhere account (free tier available)

### Deployment Steps

1. **Create a PythonAnywhere account** at [pythonanywhere.com](https://www.pythonanywhere.com)

2. **Open a Bash console** and clone your repository:
```bash
git clone https://github.com/YOUR_USERNAME/Job-Matching-AI-Platform.git
cd Job-Matching-AI-Platform
```

3. **Create a virtual environment:**
```bash
mkvirtualenv --python=/usr/bin/python3.10 job-matching-env
workon job-matching-env
```

4. **Install dependencies:**
```bash
pip install -r requirements.txt
```

5. **Configure Web App:**
   - Go to **Web** tab
   - Click **"Add a new web app"**
   - Choose **"Manual configuration"**
   - Select Python 3.10
   - Set **Source code directory:** `/home/yourusername/Job-Matching-AI-Platform`
   - Set **Working directory:** `/home/yourusername/Job-Matching-AI-Platform`

6. **Configure WSGI file:**
Click on the WSGI configuration file link and replace its contents with:

```python
import sys
import os

# Add your project directory to the sys.path
project_home = '/home/yourusername/Job-Matching-AI-Platform'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Set up the application
os.chdir(project_home)
from webapp.app import app, load_data

# Load data when the app starts
load_data()

# This is the WSGI application
application = app
```

7. **Reload the web app** from the Web tab

### Estimated Cost
- Free tier: 512MB disk, 1 web app
- Paid: Starting at $5/month

---

## VPS Deployment (Ubuntu/Debian)

Deploy on any Virtual Private Server (DigitalOcean, Linode, AWS EC2, etc.)

### Prerequisites
- VPS with Ubuntu 20.04+ or Debian 10+
- SSH access
- Domain name (optional)

### Deployment Steps

1. **Update system and install dependencies:**
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install python3 python3-pip python3-venv nginx supervisor -y
```

2. **Clone repository:**
```bash
cd /var/www
sudo git clone https://github.com/YOUR_USERNAME/Job-Matching-AI-Platform.git
cd Job-Matching-AI-Platform
```

3. **Set up virtual environment:**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

4. **Create Supervisor configuration** (`/etc/supervisor/conf.d/job-matching.conf`):
```ini
[program:job-matching-ai]
directory=/var/www/Job-Matching-AI-Platform
command=/var/www/Job-Matching-AI-Platform/venv/bin/gunicorn --bind 127.0.0.1:8000 --workers 4 --chdir webapp app:app
user=www-data
autostart=true
autorestart=true
stderr_logfile=/var/log/job-matching-ai.err.log
stdout_logfile=/var/log/job-matching-ai.out.log
```

5. **Configure Nginx** (`/etc/nginx/sites-available/job-matching`):
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static {
        alias /var/www/Job-Matching-AI-Platform/webapp/static;
        expires 30d;
    }
}
```

6. **Enable and start services:**
```bash
sudo ln -s /etc/nginx/sites-available/job-matching /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start job-matching-ai
```

7. **Set up SSL with Let's Encrypt (optional but recommended):**
```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d your-domain.com
```

### Estimated Cost
- DigitalOcean: Starting at $4/month
- Linode: Starting at $5/month
- AWS EC2: Free tier available, then variable

---

## Environment Variables

The application uses the following environment variables:

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `PORT` | Port to run the application | 5000 | No |
| `FLASK_DEBUG` | Enable debug mode (development only) | false | No |

### Setting Environment Variables

**Heroku:**
```bash
heroku config:set FLASK_DEBUG=false
```

**Railway/Render:**
Set in the dashboard under "Environment Variables"

**Docker:**
```bash
docker run -e PORT=8080 -e FLASK_DEBUG=false -p 8080:8080 job-matching-ai
```

**VPS:**
Add to supervisor configuration or create `.env` file

---

## Monitoring and Logs

### Health Check Endpoint

The application includes a health check endpoint:
```
GET /health
```

Response:
```json
{
  "status": "healthy",
  "data_loaded": true
}
```

### Viewing Logs

**Heroku:**
```bash
heroku logs --tail
```

**Railway:**
```bash
railway logs
```

**Docker:**
```bash
docker logs -f container_id
```

**VPS:**
```bash
sudo tail -f /var/log/job-matching-ai.out.log
```

---

## Performance Optimization

### Recommended Settings

- **Workers:** 2-4 (based on CPU cores)
- **Threads:** 4 per worker
- **Timeout:** 60 seconds
- **Memory:** 1GB minimum recommended

### Scaling

**Heroku:**
```bash
heroku ps:scale web=2
```

**Google Cloud Run:**
```bash
gcloud run services update job-matching-ai --max-instances=10
```

---

## Troubleshooting

### Application won't start

1. Check logs for errors
2. Verify all data files are present (jobs.csv, emplo.csv, etc.)
3. Ensure Python version is 3.9+
4. Check that all dependencies are installed

### Out of memory errors

1. Increase memory allocation
2. Reduce number of workers
3. Consider caching strategy for data

### Slow response times

1. Enable caching
2. Increase number of workers
3. Use CDN for static assets
4. Consider database for large datasets

---

## Security Considerations

1. **Always disable debug mode in production:**
   ```bash
   export FLASK_DEBUG=false
   ```

2. **Use HTTPS:** Most platforms provide automatic SSL
3. **Keep dependencies updated:** Regularly run `pip list --outdated`
4. **Environment variables:** Never commit secrets to Git
5. **Firewall:** Configure firewall rules on VPS

---

## Support

For deployment issues:
1. Check the platform-specific documentation
2. Review application logs
3. Verify all configuration files
4. Test locally with Docker first

---

## Summary

**Easiest Options:**
- 🥇 **Heroku** - One command deployment
- 🥈 **Railway** - GitHub integration, automatic deploys
- 🥉 **Render** - Free tier with auto-deploy

**Best for Containers:**
- **Docker** + **Google Cloud Run**

**Best for Python:**
- **PythonAnywhere** - Python-specific hosting

**Most Control:**
- **VPS Deployment** - Full control over server

Choose based on your needs, budget, and technical expertise!
