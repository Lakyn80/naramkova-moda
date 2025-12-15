$TAG = Get-Date -Format "yyyyMMdd-HHmm"
Write-Host ">> DEPLOY FE + BE (DB ZŮSTÁVÁ) | TAG: $TAG"

# Build images
docker build -t lakyn80/naramkova-backend:$TAG .
docker build -t lakyn80/naramkova-frontend:$TAG ./frontend

# Push images
docker push lakyn80/naramkova-backend:$TAG
docker push lakyn80/naramkova-frontend:$TAG

# Update tags on server
ssh lucky@89.221.214.140 "sed -i 's/^BACKEND_TAG=.*/BACKEND_TAG=$TAG/' /var/www/naramkova-docker/.env"
ssh lucky@89.221.214.140 "sed -i 's/^FRONTEND_TAG=.*/FRONTEND_TAG=$TAG/' /var/www/naramkova-docker/.env"

# Pull only FE + BE
ssh lucky@89.221.214.140 "cd /var/www/naramkova-docker && docker compose pull backend frontend"

# Restart only FE + BE (DB se nedotkne)
ssh lucky@89.221.214.140 "cd /var/www/naramkova-docker && docker compose up -d backend frontend"
