#!/bin/bash

PROTOCOL=$1
SCENARIO=$2
RUN=$3

if [ -z "$PROTOCOL" ] || [ -z "$SCENARIO" ] || [ -z "$RUN" ]; then
    echo "Uso: ./scripts/run_capture.sh <tcp|rudp> <A|B|C> <numero_execucao>"
    echo "Exemplo: ./scripts/run_capture.sh rudp A 1"
    exit 1
fi

mkdir -p data/pcaps

if [ "$PROTOCOL" = "tcp" ]; then
    PORT=5000
    OUTPUT_FILE="data/pcaps/tcp_${SCENARIO}_run${RUN}.pcap"
elif [ "$PROTOCOL" = "rudp" ]; then
    PORT=5001
    OUTPUT_FILE="data/pcaps/rudp_${SCENARIO}_run${RUN}.pcap"
else
    echo "Protocolo inválido. Use: tcp ou rudp."
    exit 1
fi

echo "Iniciando captura..."
echo "Protocolo: $PROTOCOL"
echo "Cenário: $SCENARIO"
echo "Execução: $RUN"
echo "Porta: $PORT"
echo "Arquivo: $OUTPUT_FILE"

tcpdump -i eth0 -w "$OUTPUT_FILE" port "$PORT"