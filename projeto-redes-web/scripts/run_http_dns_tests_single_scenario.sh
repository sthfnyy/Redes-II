#!/bin/bash

set -e

DNS_HOST="172.28.0.2"
DNS_PORT="5300"
HOST_NAME="www.sthefany.local"

TCP_PORT="8080"
RUDP_PORT="8081"

CSV_PATH="data/results/http_dns_results.csv"
OUTPUT_DIR="data/output"

REPETITIONS=10

FILES=(
  "/arquivo_100kb.bin"
  "/arquivo_1mb.bin"
  "/arquivo_10mb.bin"
)

PROTOCOLS=(
  "tcp"
  "rudp"
)

SCENARIO="${SCENARIOS_OVERRIDE:-A}"

echo "[TESTS] Rodando cenário único: $SCENARIO"

mkdir -p data/results
mkdir -p "$OUTPUT_DIR"

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
      echo "[TESTS] Cenário=$SCENARIO Protocolo=$protocol Arquivo=$file_path Execução=$run"

      if [ "$protocol" = "tcp" ]; then
        python3 -m app.web_client \
          --protocol tcp \
          --scenario "$SCENARIO" \
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
          --scenario "$SCENARIO" \
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

echo "[TESTS] Cenário $SCENARIO finalizado."

