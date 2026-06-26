# app/utils/logger.py

import csv
import os

from app.config import LOG_FILE


FIELDNAMES = [
    "protocol",
    "scenario",
    "run",
    "file_size_bytes",
    "time_seconds",
    "throughput_mbps",
    "retransmissions",
    "packets_sent",
    "acks_received",
    "total_packets",
]


def log_result(row):
    """
    Salva uma linha de resultado no arquivo CSV.
    """

    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

    file_exists = os.path.exists(LOG_FILE)

    with open(LOG_FILE, "a", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=FIELDNAMES)

        if not file_exists:
            writer.writeheader()

        writer.writerow(row)