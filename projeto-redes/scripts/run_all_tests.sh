#!/bin/bash

RUNS=${1:-10}

PROTOCOLS=("tcp" "rudp")
SCENARIOS=("A" "B" "C")

SERVER_CONTAINER="redes_server"
CLIENT_CONTAINER="redes_client"

SERVER_IP="172.28.0.2"
INPUT_FILE="data/input/arquivo_teste.bin"

echo "======================================"
echo "Iniciando bateria de testes"
echo "Execuções por protocolo/cenário: $RUNS"
echo "Protocolos: TCP e R-UDP"
echo "Cenários: A, B e C"
echo "======================================"

mkdir -p data/logs
mkdir -p data/pcaps
mkdir -p data/received

for PROTOCOL in "${PROTOCOLS[@]}"; do
    for SCENARIO in "${SCENARIOS[@]}"; do
        for RUN in $(seq 1 "$RUNS"); do

            echo ""
            echo "--------------------------------------"
            echo "Teste: $PROTOCOL | Cenário: $SCENARIO | Execução: $RUN"
            echo "--------------------------------------"

            if [ "$PROTOCOL" = "tcp" ]; then
                PORT=5000
                PCAP_FILE="data/pcaps/tcp_${SCENARIO}_run${RUN}.pcap"
                RECEIVED_FILE="data/received/tcp_${SCENARIO}_run${RUN}.bin"
                SERVER_LOG="data/logs/server_tcp_${SCENARIO}_run${RUN}.log"
            else
                PORT=5001
                PCAP_FILE="data/pcaps/rudp_${SCENARIO}_run${RUN}.pcap"
                RECEIVED_FILE="data/received/rudp_${SCENARIO}_run${RUN}.bin"
                SERVER_LOG="data/logs/server_rudp_${SCENARIO}_run${RUN}.log"
            fi

            echo "[1/6] Limpando processos antigos no servidor..."
            docker exec "$SERVER_CONTAINER" bash -lc "pkill -f 'python3 -m app.server' 2>/dev/null || true"
            docker exec "$SERVER_CONTAINER" bash -lc "pkill -2 tcpdump 2>/dev/null || true"
            sleep 1

            echo "[2/6] Removendo arquivos antigos deste teste..."
            rm -f "$PCAP_FILE"
            rm -f "$RECEIVED_FILE"
            rm -f "$SERVER_LOG"

            echo "[3/6] Iniciando captura tcpdump..."
            docker exec -d "$SERVER_CONTAINER" bash -lc "
                cd /workspace &&
                tcpdump -i eth0 -w '$PCAP_FILE' port $PORT > data/logs/tcpdump_${PROTOCOL}_${SCENARIO}_run${RUN}.log 2>&1
            "

            sleep 1

            echo "[4/6] Iniciando servidor..."
            docker exec -d "$SERVER_CONTAINER" bash -lc "
                cd /workspace &&
                ./scripts/run_server.sh $PROTOCOL $SCENARIO $RUN > '$SERVER_LOG' 2>&1
            "

            sleep 1

            echo "[5/6] Executando cliente..."
            docker exec "$CLIENT_CONTAINER" bash -lc "
                cd /workspace &&
                ./scripts/run_client.sh $PROTOCOL $SCENARIO $RUN $SERVER_IP $INPUT_FILE
            "

            echo "[6/6] Encerrando captura tcpdump..."
            docker exec "$SERVER_CONTAINER" bash -lc "pkill -2 tcpdump 2>/dev/null || true"

            sleep 1

            echo "Verificando arquivos gerados..."

            if [ -f "$PCAP_FILE" ]; then
                echo "PCAP criado: $PCAP_FILE"
            else
                echo "AVISO: PCAP não encontrado: $PCAP_FILE"
            fi

            if [ -f "$RECEIVED_FILE" ]; then
                echo "Arquivo recebido: $RECEIVED_FILE"
            else
                echo "AVISO: Arquivo recebido não encontrado: $RECEIVED_FILE"
            fi

            echo "Teste finalizado: $PROTOCOL $SCENARIO run $RUN"

        done
    done
done

echo ""
echo "======================================"
echo "Todos os testes foram finalizados."
echo "Resultados em: data/logs/results.csv"
echo "Capturas em: data/pcaps/"
echo "Arquivos recebidos em: data/received/"
echo "======================================"