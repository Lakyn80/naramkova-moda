$TAG = Get-Date -Format "yyyyMMdd-HHmm"
Write-Host ">> Použitý TAG: $TAG"

# Stop & remove local containers
docker stop nmm-backend, nmm-frontend 2>$null
docker rm nmm-backend, nmm-frontend 2>$null

# Clean local images
docker image prune -f

# Build images with TAG
docker build -t lakyn80/naramkova-backend:$TAG .
docker build -t lakyn80/naramkova-frontend:$TAG ./frontend

# Push to Docker Hub
docker push lakyn80/naramkova-backend:$TAG
docker push lakyn80/naramkova-frontend:$TAG

# Update .env on server
ssh lucky@89.221.214.140 "echo BACKEND_TAG=$TAG > /var/www/naramkova-docker/.env"
ssh lucky@89.221.214.140 "echo FRONTEND_TAG=$TAG >> /var/www/naramkova-docker/.env"

# Deploy on server
ssh lucky@89.221.214.140 "cd /var/www/naramkova-docker && docker compose pull && docker compose up -d"
