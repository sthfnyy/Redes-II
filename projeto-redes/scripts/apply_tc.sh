#!/bin/bash

SCENARIO=$1
INTERFACE=${2:-eth0}

tc qdisc del dev "$INTERFACE" root 2>/dev/null

if [ "$SCENARIO" = "A" ]; then
    tc qdisc add dev "$INTERFACE" root netem delay 10ms loss 0%
elif [ "$SCENARIO" = "B" ]; then
    tc qdisc add dev "$INTERFACE" root netem delay 50ms loss 5%
elif [ "$SCENARIO" = "C" ]; then
    tc qdisc add dev "$INTERFACE" root netem delay 100ms loss 10%
else
    echo "Cenário inválido. Use: A, B ou C."
    exit 1
fi

echo "Cenário $SCENARIO aplicado na interface $INTERFACE."
tc qdisc show dev "$INTERFACE"