#!/bin/bash

PROTOCOL=$1
SCENARIO=$2
RUN=$3
SERVER_IP=${4:-172.28.0.2}
INPUT_FILE=${5:-data/input/arquivo_teste.bin}

if [ -z "$PROTOCOL" ] || [ -z "$SCENARIO" ] || [ -z "$RUN" ]; then
    echo "Uso: ./scripts/run_client.sh <tcp|rudp> <A|B|C> <numero_execucao> [server_ip] [arquivo]"
    echo "Exemplo: ./scripts/run_client.sh rudp A 1"
    echo "Exemplo com IP: ./scripts/run_client.sh rudp B 2 172.28.0.2"
    exit 1
fi

if [ ! -f "$INPUT_FILE" ]; then
    echo "Arquivo de entrada não encontrado: $INPUT_FILE"
    exit 1
fi

echo "Aplicando cenário $SCENARIO..."
./scripts/apply_tc.sh "$SCENARIO"

if [ "$PROTOCOL" = "tcp" ]; then
    echo "Iniciando cliente TCP..."

    python3 -m app.client \
      --protocol tcp \
      --host "$SERVER_IP" \
      --file "$INPUT_FILE" \
      --scenario "$SCENARIO" \
      --run "$RUN"

elif [ "$PROTOCOL" = "rudp" ]; then
    echo "Iniciando cliente R-UDP..."

    python3 -m app.client \
      --protocol rudp \
      --host "$SERVER_IP" \
      --file "$INPUT_FILE" \
      --scenario "$SCENARIO" \
      --run "$RUN"

else
    echo "Protocolo inválido. Use: tcp ou rudp."
    exit 1
fi