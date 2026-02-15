#!/bin/bash
# Deployment Verification Script for Job Matching AI Platform

echo "🔍 Verifying Job Matching AI Platform Deployment Files..."
echo ""

# Check if all required files exist
FILES=(
    "Dockerfile"
    "docker-compose.yml"
    ".dockerignore"
    "Procfile"
    "runtime.txt"
    "render.yaml"
    "requirements.txt"
    "requirements-prod.txt"
    "DEPLOYMENT.md"
    "webapp/app.py"
    "data/jobs.csv"
    "data/emplo.csv"
)

MISSING=0

for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file"
    else
        echo "❌ $file (MISSING)"
        MISSING=$((MISSING + 1))
    fi
done

echo ""

# Check for health endpoint
if grep -q "@app.route('/health')" webapp/app.py; then
    echo "✅ Health check endpoint configured"
else
    echo "❌ Health check endpoint missing"
    MISSING=$((MISSING + 1))
fi

# Check for PORT environment variable
if grep -q "PORT" webapp/app.py; then
    echo "✅ PORT environment variable support"
else
    echo "❌ PORT environment variable support missing"
    MISSING=$((MISSING + 1))
fi

# Check for gunicorn in requirements
if grep -q "gunicorn" requirements.txt; then
    echo "✅ Gunicorn in requirements.txt"
else
    echo "❌ Gunicorn missing from requirements.txt"
    MISSING=$((MISSING + 1))
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ $MISSING -eq 0 ]; then
    echo "✅ All deployment files verified successfully!"
    echo ""
    echo "🚀 Ready to deploy! Choose your platform:"
    echo ""
    echo "  Docker:    docker-compose up -d"
    echo "  Heroku:    git push heroku main"
    echo "  Railway:   Connect GitHub repo in dashboard"
    echo "  Render:    Connect GitHub repo and auto-deploy"
    echo ""
    echo "📖 See DEPLOYMENT.md for detailed instructions"
    exit 0
else
    echo "⚠️  Found $MISSING issue(s)"
    echo "Please check the missing files/configurations"
    exit 1
fi
