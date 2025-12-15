param(
    [ValidateSet("with-db", "no-db")]
    [string]$mode
)

if (-not $mode) {
    Write-Host "Použití: .\compose-deploy.ps1 with-db | no-db"
    exit 1
}

$TAG = Get-Date -Format "yyyyMMdd-HHmm"
Write-Host ">> DEPLOY MODE: $mode | TAG: $TAG"

# Build images
docker build -t lakyn80/naramkova-backend:$TAG .
docker build -t lakyn80/naramkova-frontend:$TAG ./frontend

# Push images
docker push lakyn80/naramkova-backend:$TAG
docker push lakyn80/naramkova-frontend:$TAG

# Update .env on server
ssh lucky@89.221.214.140 "echo BACKEND_TAG=$TAG > /var/www/naramkova-docker/.env"
ssh lucky@89.221.214.140 "echo FRONTEND_TAG=$TAG >> /var/www/naramkova-docker/.env"

# Select compose file
if ($mode -eq "with-db") {
    $composeFile = "docker-compose.with-db.yml"
} else {
    $composeFile = "docker-compose.no-db.yml"
}

# Deploy
ssh lucky@89.221.214.140 `
"cd /var/www/naramkova-docker && \
 docker compose -f $composeFile pull && \
 docker compose -f $composeFile up -d"
