# 🚀 Quick Start - Hosting Guide

This guide will get your Job Matching AI Platform hosted in minutes!

## Choose Your Platform

### 1. 🐳 Docker (Fastest - 2 minutes)

**Prerequisites:** Docker installed

```bash
# Clone repository
git clone https://github.com/YOUR_USERNAME/Job-Matching-AI-Platform.git
cd Job-Matching-AI-Platform

# Start with Docker Compose
docker-compose up -d

# Open http://localhost:8080
```

**Stop:**
```bash
docker-compose down
```

---

### 2. ☁️ Heroku (Easiest - 5 minutes)

**Prerequisites:** Heroku account and CLI

```bash
# Login
heroku login

# Create app
heroku create your-app-name

# Deploy
git push heroku main

# Open app
heroku open
```

**Cost:** Free tier (550 hours/month)

---

### 3. 🚂 Railway (Most Modern - 3 minutes)

**Prerequisites:** Railway account

1. Go to [railway.app](https://railway.app)
2. Click **"New Project"** → **"Deploy from GitHub repo"**
3. Select this repository
4. Click **"Deploy"**
5. Done! Your app is live

**Cost:** $5 free credit/month

---

### 4. 🎨 Render (Best Free Option)

**Prerequisites:** Render account

1. Go to [render.com](https://render.com)
2. Click **"New +"** → **"Web Service"**
3. Connect GitHub repository
4. Render will auto-detect configuration from `render.yaml`
5. Click **"Create Web Service"**

**Cost:** Free tier available

---

### 5. ☁️ Google Cloud Run (Serverless - 10 minutes)

**Prerequisites:** Google Cloud account, gcloud CLI

```bash
# Authenticate
gcloud auth login
gcloud config set project YOUR_PROJECT_ID

# Build and deploy
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/job-matching-ai

gcloud run deploy job-matching-ai \
  --image gcr.io/YOUR_PROJECT_ID/job-matching-ai \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --port 8080
```

**Cost:** Free tier (2 million requests/month)

---

### 6. 🐍 PythonAnywhere (Python-Focused - 15 minutes)

**Prerequisites:** PythonAnywhere account

1. Sign up at [pythonanywhere.com](https://www.pythonanywhere.com)
2. Open Bash console:
   ```bash
   git clone https://github.com/YOUR_USERNAME/Job-Matching-AI-Platform.git
   cd Job-Matching-AI-Platform
   mkvirtualenv --python=/usr/bin/python3.10 job-matching-env
   pip install -r requirements.txt
   ```
3. Configure Web app in dashboard
4. Update WSGI file (see DEPLOYMENT.md)
5. Reload app

**Cost:** Free tier (512MB)

---

## Platform Comparison

| Platform | Setup Time | Free Tier | Best For |
|----------|-----------|-----------|----------|
| Docker | 2 min | N/A | Local testing |
| Heroku | 5 min | 550 hrs/mo | Quick deploy |
| Railway | 3 min | $5 credit | Auto-deploy from GitHub |
| Render | 5 min | Limited | Free production hosting |
| Google Cloud Run | 10 min | 2M req/mo | Serverless scalability |
| PythonAnywhere | 15 min | 512MB | Python apps |

---

## Environment Variables

Set these for production:

```bash
# Heroku
heroku config:set FLASK_DEBUG=false

# Railway/Render
# Set in dashboard under Environment Variables

# Docker
docker run -e FLASK_DEBUG=false -e PORT=8080 job-matching-ai
```

---

## Health Check

All platforms can use this endpoint for monitoring:

```
GET /health

Response:
{
  "status": "healthy",
  "data_loaded": true
}
```

---

## Troubleshooting

**App won't start?**
- Check logs on your platform
- Verify data files are present
- Ensure Python 3.9+

**Out of memory?**
- Increase memory allocation (platform-specific)
- Use fewer workers

**Need help?**
- Check [DEPLOYMENT.md](DEPLOYMENT.md) for detailed guides
- Review platform-specific documentation

---

## Next Steps

1. ✅ Choose a platform above
2. ✅ Follow the quick start for that platform
3. ✅ Test your deployed app at the provided URL
4. ✅ Share your hosted application!

For detailed instructions, monitoring, and optimization, see **[DEPLOYMENT.md](DEPLOYMENT.md)**.

---

**Happy Hosting! 🎉**
