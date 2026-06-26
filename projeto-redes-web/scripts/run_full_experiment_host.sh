#!/bin/bash

set -e

PROJECT_DIR="/workspace"
CLIENT_CONTAINER="redes_web_client"
SERVER_CONTAINER="redes_web_server"
DNS_CONTAINER="redes_dns"

echo "[HOST] Limpando resultados antigos..."
rm -f data/results/http_dns_results.csv
rm -rf data/output/*
mkdir -p data/results data/output

echo "[HOST] Reiniciando DNS..."
docker exec "$DNS_CONTAINER" pkill -f "app.dns_server" || true
docker exec -d "$DNS_CONTAINER" python3 -m app.dns_server \
  --host 0.0.0.0 \
  --port 5300 \
  --hosts-file dns/hosts.txt

echo "[HOST] Reiniciando servidores Web TCP e R-UDP..."
docker exec "$SERVER_CONTAINER" pkill -f "app.web_server" || true

docker exec -d "$SERVER_CONTAINER" python3 -m app.web_server \
  --mode tcp \
  --host 0.0.0.0 \
  --port 8080 \
  --www-dir app/www

docker exec -d "$SERVER_CONTAINER" python3 -m app.web_server \
  --mode rudp \
  --host 0.0.0.0 \
  --port 8081 \
  --www-dir app/www

sleep 2

echo "[HOST] Processos ativos:"
docker exec "$DNS_CONTAINER" pgrep -af "dns_server" || true
docker exec "$SERVER_CONTAINER" pgrep -af "web_server" || true

SCENARIOS=("A" "B" "C")

for scenario in "${SCENARIOS[@]}"; do
  echo ""
  echo "=================================================="
  echo "[HOST] Cenário $scenario"
  echo "=================================================="

  echo "[HOST] Limpando tc anterior..."
  docker exec "$SERVER_CONTAINER" bash scripts/clear_tc.sh eth0 || true

  echo "[HOST] Aplicando tc no web_server..."
  docker exec "$SERVER_CONTAINER" bash scripts/apply_tc.sh "$scenario" eth0

  echo "[HOST] Rodando testes do cenário $scenario no cliente..."
  docker exec "$CLIENT_CONTAINER" bash -lc "
    SCENARIOS_OVERRIDE=$scenario ./scripts/run_http_dns_tests_single_scenario.sh
  "
done

echo "[HOST] Limpando tc final..."
docker exec "$SERVER_CONTAINER" bash scripts/clear_tc.sh eth0 || true

echo "[HOST] Experimento completo finalizado."
echo "[HOST] Resultados em: data/results/http_dns_results.csv"

