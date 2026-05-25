#!/bin/bash

PROTOCOL=$1
SCENARIO=$2
RUN=$3

if [ -z "$PROTOCOL" ] || [ -z "$SCENARIO" ] || [ -z "$RUN" ]; then
    echo "Uso: ./scripts/run_server.sh <tcp|rudp> <A|B|C> <numero_execucao>"
    echo "Exemplo: ./scripts/run_server.sh rudp A 1"
    exit 1
fi

mkdir -p data/received

if [ "$PROTOCOL" = "tcp" ]; then
    OUTPUT_FILE="data/received/tcp_${SCENARIO}_run${RUN}.bin"

    echo "Iniciando servidor TCP..."
    echo "Arquivo de saída: $OUTPUT_FILE"

    python3 -m app.server \
      --protocol tcp \
      --host 0.0.0.0 \
      --output "$OUTPUT_FILE"

elif [ "$PROTOCOL" = "rudp" ]; then
    OUTPUT_FILE="data/received/rudp_${SCENARIO}_run${RUN}.bin"

    echo "Iniciando servidor R-UDP..."
    echo "Arquivo de saída: $OUTPUT_FILE"

    python3 -m app.server \
      --protocol rudp \
      --host 0.0.0.0 \
      --output "$OUTPUT_FILE"

else
    echo "Protocolo inválido. Use: tcp ou rudp."
    exit 1
fi