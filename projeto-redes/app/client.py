# app/client.py

import argparse
import os
import time

from app.config import TCP_PORT, RUDP_PORT
from app.protocols.tcp_transfer import send_file_tcp
from app.utils.logger import log_result

from app.protocols.rudp_gbn import send_file_rudp_gbn

def main():
    """
    Programa principal do cliente.

    Ele recebe argumentos pela linha de comando, envia o arquivo
    usando o protocolo escolhido, calcula métricas e salva no CSV.
    """

    parser = argparse.ArgumentParser(
        description="Cliente de transferência de arquivos TCP/R-UDP"
    )

    parser.add_argument(
        "--protocol",
        choices=["tcp", "rudp"],
        required=True,
        help="Protocolo usado na transferência: tcp ou rudp",
    )

    parser.add_argument(
        "--host",
        required=True,
        help="IP ou nome do servidor",
    )

    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="Porta do servidor",
    )

    parser.add_argument(
        "--file",
        required=True,
        help="Arquivo que será enviado",
    )

    parser.add_argument(
        "--scenario",
        required=True,
        help="Cenário de teste: A, B ou C",
    )

    parser.add_argument(
        "--run",
        type=int,
        required=True,
        help="Número da execução",
    )

    args = parser.parse_args()

    if args.port is None:
        if args.protocol == "tcp":
            args.port = TCP_PORT
        else:
            args.port = RUDP_PORT

    file_size = os.path.getsize(args.file)

    start_time = time.time()

    if args.protocol == "tcp":
        stats = send_file_tcp(args.host, args.port, args.file)

    elif args.protocol == "rudp":
        stats = send_file_rudp_gbn(args.host, args.port, args.file)

    end_time = time.time()

    elapsed = end_time - start_time
    throughput_mbps = (file_size * 8) / elapsed / 1_000_000

    log_result({
        "protocol": args.protocol.upper(),
        "scenario": args.scenario,
        "run": args.run,
        "file_size_bytes": file_size,
        "time_seconds": round(elapsed, 6),
        "throughput_mbps": round(throughput_mbps, 6),
        "retransmissions": stats.get("retransmissions", 0),
        "packets_sent": stats.get("packets_sent", 0),
        "acks_received": stats.get("acks_received", 0),
        "total_packets": stats.get("total_packets", 0),
    })

    print("Transferência finalizada.")
    print(f"Protocolo: {args.protocol.upper()}")
    print(f"Cenário: {args.scenario}")
    print(f"Execução: {args.run}")
    print(f"Tamanho: {file_size} bytes")
    print(f"Tempo: {elapsed:.6f} segundos")
    print(f"Throughput: {throughput_mbps:.6f} Mbps")


if __name__ == "__main__":
    main()