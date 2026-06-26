#!/bin/bash

PCAP=$1

if [ -z "$PCAP" ]; then
    echo "Uso: ./analysis/pcap_summary.sh <arquivo.pcap>"
    echo "Exemplo: ./analysis/pcap_summary.sh data/pcaps/rudp_C_run1.pcap"
    exit 1
fi

if [ ! -f "$PCAP" ]; then
    echo "Arquivo PCAP não encontrado: $PCAP"
    exit 1
fi

echo "Resumo do PCAP:"
echo "Arquivo: $PCAP"
echo ""

capinfos "$PCAP"