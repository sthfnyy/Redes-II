#!/bin/bash

ORIGINAL=${1:-data/input/arquivo_teste.bin}
RECEIVED=${2}

if [ -z "$RECEIVED" ]; then
    echo "Uso: ./scripts/check_integrity.sh <arquivo_original> <arquivo_recebido>"
    echo "Exemplo:"
    echo "./scripts/check_integrity.sh data/input/arquivo_teste.bin data/received/rudp_C_run1.bin"
    exit 1
fi

if [ ! -f "$ORIGINAL" ]; then
    echo "Arquivo original não encontrado: $ORIGINAL"
    exit 1
fi

if [ ! -f "$RECEIVED" ]; then
    echo "Arquivo recebido não encontrado: $RECEIVED"
    exit 1
fi

HASH_ORIGINAL=$(sha256sum "$ORIGINAL" | awk '{print $1}')
HASH_RECEIVED=$(sha256sum "$RECEIVED" | awk '{print $1}')

echo "Hash original: $HASH_ORIGINAL"
echo "Hash recebido: $HASH_RECEIVED"

if [ "$HASH_ORIGINAL" = "$HASH_RECEIVED" ]; then
    echo "Integridade OK: os arquivos são idênticos."
else
    echo "ERRO: os arquivos são diferentes."
    exit 1
fi