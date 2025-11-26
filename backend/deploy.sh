#!/bin/bash
# Quick deployment script for production

set -e

echo "🚀 Starting deployment..."

# Check if .env.production exists
if [ ! -f .env.production ]; then
    echo "❌ Error: .env.production file not found!"
    echo "Please create .env.production with your production environment variables."
    exit 1
fi

# Pull latest code (if using git)
# git pull

# Build and start services
echo "📦 Building and starting services..."
docker compose -f docker-compose.prod.yml up -d --build

# Wait for services to be healthy
echo "⏳ Waiting for services to be healthy..."
sleep 10

# Check health
echo "🏥 Checking service health..."
curl -f http://localhost:8080/health || echo "⚠️  Health check failed, but services may still be starting..."

echo "✅ Deployment complete!"
echo "📊 View logs with: docker compose -f docker-compose.prod.yml logs -f"
echo "🛑 Stop services with: docker compose -f docker-compose.prod.yml down"


