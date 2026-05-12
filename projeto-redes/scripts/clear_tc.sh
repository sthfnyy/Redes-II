#!/bin/bash

INTERFACE=${1:-eth0}

tc qdisc del dev "$INTERFACE" root 2>/dev/null

echo "Regras tc removidas da interface $INTERFACE."
tc qdisc show dev "$INTERFACE"