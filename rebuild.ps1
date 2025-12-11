# Zastavení kontejnerů (ignoruj chyby, pokud neběží)
docker stop nmm-backend, nmm-frontend 2>$null

# Smazání kontejnerů (ignoruj chyby, pokud neexistují)
docker rm nmm-backend, nmm-frontend 2>$null

# Vyčištění nepotřebných image (bez dotazu)
docker image prune -f

# Znovupostavení a spuštění služby
docker compose up -d --build
