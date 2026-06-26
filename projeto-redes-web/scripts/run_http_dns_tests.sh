#!/bin/bash

set -e

DNS_HOST="172.28.0.2"
DNS_PORT="5300"
HOST_NAME="www.sthefany.local"

TCP_PORT="8080"
RUDP_PORT="8081"

CSV_PATH="data/results/http_dns_results.csv"
OUTPUT_DIR="data/output"

REPETITIONS=1

FILES=(
  "/arquivo_100kb.bin"
  "/arquivo_1mb.bin"
  "/arquivo_10mb.bin"
)

PROTOCOLS=(
  "tcp"
  "rudp"
)

SCENARIOS=(
  "A"
  "B"
  "C"
)

echo "[TESTS] Iniciando bateria de testes HTTP + DNS"
echo "[TESTS] CSV: $CSV_PATH"
echo "[TESTS] Output: $OUTPUT_DIR"

mkdir -p data/results
mkdir -p "$OUTPUT_DIR"

for scenario in "${SCENARIOS[@]}"; do
  echo ""
  echo "=================================================="
  echo "[TESTS] Aplicando cenário $scenario no web_server"
  echo "=================================================="

  if [ "$scenario" = "A" ]; then
    DELAY="10ms"
    LOSS="0%"
  elif [ "$scenario" = "B" ]; then
    DELAY="50ms"
    LOSS="5%"
  elif [ "$scenario" = "C" ]; then
    DELAY="100ms"
    LOSS="10%"
  else
    echo "[TESTS] Cenário inválido: $scenario"
    exit 1
  fi

  # Aplica perda/delay na saída do container web_server.
  # O script é executado dentro do web_client, então usamos ssh? Não.
  # Como docker não existe dentro do container, esta parte será usada
  # quando o script for executado pelo host com docker exec.
  echo "[TESTS] Cenário $scenario = delay $DELAY, loss $LOSS"
  echo "[TESTS] Aplicar manualmente no host antes deste bloco se necessário."

  for protocol in "${PROTOCOLS[@]}"; do
    echo ""
    echo "------------------------------------------"
    echo "[TESTS] Protocolo: $protocol"
    echo "------------------------------------------"

    for file_path in "${FILES[@]}"; do
      echo ""
      echo "[TESTS] Arquivo: $file_path"

      for run in $(seq 1 $REPETITIONS); do
        echo ""
        echo "[TESTS] Cenário=$scenario Protocolo=$protocol Arquivo=$file_path Execução=$run"

        if [ "$protocol" = "tcp" ]; then
          python3 -m app.web_client \
            --protocol tcp \
            --scenario "$scenario" \
            --run "$run" \
            --dns-host "$DNS_HOST" \
            --dns-port "$DNS_PORT" \
            --host-name "$HOST_NAME" \
            --path "$file_path" \
            --tcp-port "$TCP_PORT" \
            --output-dir "$OUTPUT_DIR" \
            --csv-path "$CSV_PATH"
        else
          python3 -m app.web_client \
            --protocol rudp \
            --scenario "$scenario" \
            --run "$run" \
            --dns-host "$DNS_HOST" \
            --dns-port "$DNS_PORT" \
            --host-name "$HOST_NAME" \
            --path "$file_path" \
            --rudp-port "$RUDP_PORT" \
            --output-dir "$OUTPUT_DIR" \
            --csv-path "$CSV_PATH"
        fi

        sleep 0.5
      done
    done
  done
done

echo ""
echo "[TESTS] Bateria de testes finalizada."
echo "[TESTS] Resultados salvos em: $CSV_PATH"