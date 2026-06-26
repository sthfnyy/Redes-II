# app/web_client.py

import argparse
import csv
import socket
import time
from pathlib import Path

from app.dns_client import resolve_name
from app.protocols.http_parser import (
    build_http_get_request,
    split_http_response,
    parse_status_code,
)

from app.protocols.rudp_gbn import (
    send_bytes_rudp_gbn,
    receive_bytes_rudp_gbn,
)

def ensure_parent_dir(path: str):
    Path(path).parent.mkdir(parents=True, exist_ok=True)


def receive_all_tcp(sock: socket.socket, buffer_size: int = 4096) -> bytes:
    response = b""

    while True:
        chunk = sock.recv(buffer_size)

        if not chunk:
            break

        response += chunk

    return response


def write_result_csv(csv_path: str, row: dict):
    ensure_parent_dir(csv_path)

    fieldnames = [
        "timestamp",
        "protocol",
        "scenario",
        "file_name",
        "file_size_bytes",
        "run",
        "dns_time_ms",
        "dns_attempts",
        "http_time_ms",
        "total_time_ms",
        "throughput_mbps",
        "status_code",
        "http_header_bytes",
        "http_body_bytes",
        "response_total_bytes",
        "retransmissions",
        "packets_sent",
        "acks_received",
        "success",
    ]

    file_exists = Path(csv_path).exists()

    with open(csv_path, "a", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)

        if not file_exists:
            writer.writeheader()

        writer.writerow(row)


def save_response_body(output_dir: str, protocol: str, scenario: str, run: int, path: str, body: bytes):
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    file_name = Path(path).name

    if not file_name:
        file_name = "index.html"

    saved_file = output_path / f"{protocol}_{scenario}_run{run}_{file_name}"
    saved_file.write_bytes(body)

    return saved_file

def receive_all_tcp(sock: socket.socket, buffer_size: int = 4096) -> bytes:
    """
    Recebe todos os bytes de uma conexão TCP até o servidor fechar a conexão.
    """

    response = b""

    while True:
        chunk = sock.recv(buffer_size)

        if not chunk:
            break

        response += chunk

    return response


def http_get_tcp(
    server_ip: str,
    server_port: int,
    host_name: str,
    path: str,
    buffer_size: int = 4096,
):
    """
    Faz uma requisição HTTP GET usando TCP nativo.
    """

    request = build_http_get_request(
        host=host_name,
        path=path,
    )

    start_http = time.perf_counter()

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((server_ip, server_port))
    sock.sendall(request)

    response = receive_all_tcp(sock, buffer_size=buffer_size)

    sock.close()

    end_http = time.perf_counter()

    http_time_ms = (end_http - start_http) * 1000

    header, body = split_http_response(response)
    status_code = parse_status_code(header)

    return {
        "response": response,
        "header": header,
        "body": body,
        "status_code": status_code,
        "http_time_ms": http_time_ms,
        "http_header_bytes": len(header),
        "http_body_bytes": len(body),
        "response_total_bytes": len(response),
    }

def http_get_rudp(
    server_ip: str,
    server_port: int,
    host_name: str,
    path: str,
):
    """
    Faz uma requisição HTTP GET usando R-UDP como transporte.

    Fluxo:
    1. Monta GET HTTP/1.1.
    2. Envia o GET via R-UDP.
    3. Recebe a resposta HTTP via R-UDP.
    4. Separa cabeçalho e corpo.
    """

    request = build_http_get_request(
        host=host_name,
        path=path,
    )

    server_address = (server_ip, server_port)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    start_http = time.perf_counter()

    send_metrics = send_bytes_rudp_gbn(
        sock=sock,
        address=server_address,
        data=request,
    )

    received = receive_bytes_rudp_gbn(sock)

    end_http = time.perf_counter()

    sock.close()

    response = received["data"]

    http_time_ms = (end_http - start_http) * 1000

    header, body = split_http_response(response)
    status_code = parse_status_code(header)

    return {
        "response": response,
        "header": header,
        "body": body,
        "status_code": status_code,
        "http_time_ms": http_time_ms,
        "http_header_bytes": len(header),
        "http_body_bytes": len(body),
        "response_total_bytes": len(response),

        # Métricas do GET enviado pelo cliente
        "request_packets_sent": send_metrics["packets_sent"],
        "request_acks_received": send_metrics["acks_received"],
        "request_retransmissions": send_metrics["retransmissions"],

        # Métricas da resposta recebida do servidor
        "response_packets_received": received["packets_received"],
        "response_acks_sent": received["acks_sent"],

        # Campos antigos mantidos para compatibilidade com o CSV atual
        "retransmissions": send_metrics["retransmissions"],
        "packets_sent": received["packets_received"],
        "acks_received": received["acks_sent"],
    }


def run_web_client(args):
    total_start = time.perf_counter()

    dns_result = resolve_name(
        dns_host=args.dns_host,
        dns_port=args.dns_port,
        name=args.host_name,
        timeout=args.dns_timeout,
        retries=args.dns_retries,
    )

    if not dns_result["success"]:
        total_end = time.perf_counter()
        total_time_ms = (total_end - total_start) * 1000

        row = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "protocol": args.protocol.upper(),
            "scenario": args.scenario,
            "file_name": args.path,
            "file_size_bytes": 0,
            "run": args.run,
            "dns_time_ms": dns_result["dns_time_ms"],
            "dns_attempts": dns_result["dns_attempts"],
            "http_time_ms": 0,
            "total_time_ms": total_time_ms,
            "throughput_mbps": 0,
            "status_code": 0,
            "http_header_bytes": 0,
            "http_body_bytes": 0,
            "response_total_bytes": 0,
            "retransmissions": 0,
            "packets_sent": 0,
            "acks_received": 0,
            "success": False,
        }

        write_result_csv(args.csv_path, row)

        print("[WEB CLIENT] Falha na resolução DNS. Requisição HTTP não será feita.")
        return

    server_ip = dns_result["ip"]

    print(f"[WEB CLIENT] IP resolvido para o servidor Web: {server_ip}")

    if args.protocol.lower() == "tcp":
        http_result = http_get_tcp(
            server_ip=server_ip,
            server_port=args.tcp_port,
            host_name=args.host_name,
            path=args.path,
            buffer_size=args.buffer_size,
        )

        retransmissions = 0
        packets_sent = 0
        acks_received = 0

    elif args.protocol.lower() == "rudp":
        http_result = http_get_rudp(
            server_ip=server_ip,
            server_port=args.rudp_port,
            host_name=args.host_name,
            path=args.path,
        )

        retransmissions = http_result["retransmissions"]
        packets_sent = http_result["packets_sent"]
        acks_received = http_result["acks_received"]

    else:
        raise ValueError(f"Protocolo inválido: {args.protocol}")
    

    total_end = time.perf_counter()
    total_time_ms = (total_end - total_start) * 1000

    body_bytes = http_result["http_body_bytes"]

    if total_time_ms > 0:
        throughput_mbps = (body_bytes * 8) / (total_time_ms / 1000) / 1_000_000
    else:
        throughput_mbps = 0

    success = http_result["status_code"] == 200

    saved_file = save_response_body(
        output_dir=args.output_dir,
        protocol=args.protocol.lower(),
        scenario=args.scenario,
        run=args.run,
        path=args.path,
        body=http_result["body"],
    )

    row = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "protocol": args.protocol.upper(),
        "scenario": args.scenario,
        "file_name": args.path,
        "file_size_bytes": body_bytes,
        "run": args.run,
        "dns_time_ms": dns_result["dns_time_ms"],
        "dns_attempts": dns_result["dns_attempts"],
        "http_time_ms": http_result["http_time_ms"],
        "total_time_ms": total_time_ms,
        "throughput_mbps": throughput_mbps,
        "status_code": http_result["status_code"],
        "http_header_bytes": http_result["http_header_bytes"],
        "http_body_bytes": http_result["http_body_bytes"],
        "response_total_bytes": http_result["response_total_bytes"],
        "retransmissions": retransmissions,
        "packets_sent": packets_sent,
        "acks_received": acks_received,
        "success": success,
    }

    write_result_csv(args.csv_path, row)

    print("[WEB CLIENT] Requisição finalizada")
    print(f"[WEB CLIENT] Protocolo: {args.protocol.upper()}")
    print(f"[WEB CLIENT] Cenário: {args.scenario}")
    print(f"[WEB CLIENT] Caminho: {args.path}")
    print(f"[WEB CLIENT] Status HTTP: {http_result['status_code']}")
    print(f"[WEB CLIENT] Tempo DNS: {dns_result['dns_time_ms']:.3f} ms")
    print(f"[WEB CLIENT] Tempo HTTP: {http_result['http_time_ms']:.3f} ms")
    print(f"[WEB CLIENT] Tempo total: {total_time_ms:.3f} ms")
    print(f"[WEB CLIENT] Corpo recebido: {body_bytes} bytes")
    print(f"[WEB CLIENT] Cabeçalho HTTP: {http_result['http_header_bytes']} bytes")
    print(f"[WEB CLIENT] Resposta total: {http_result['response_total_bytes']} bytes")
    print(f"[WEB CLIENT] Throughput total com DNS: {throughput_mbps:.6f} Mbps")
    print(f"[WEB CLIENT] Arquivo salvo em: {saved_file}")


def main():
    parser = argparse.ArgumentParser(
        description="Cliente Web simplificado com resolução DNS local."
    )

    parser.add_argument("--protocol", choices=["tcp", "rudp"], default="tcp")
    parser.add_argument("--scenario", default="A")
    parser.add_argument("--run", type=int, default=1)

    parser.add_argument("--dns-host", default="172.28.0.2")
    parser.add_argument("--dns-port", type=int, default=5300)
    parser.add_argument("--dns-timeout", type=float, default=1.0)
    parser.add_argument("--dns-retries", type=int, default=3)

    parser.add_argument("--host-name", default="www.sthefany.local")
    parser.add_argument("--path", default="/index.html")

    parser.add_argument("--tcp-port", type=int, default=8080)
    parser.add_argument("--rudp-port", type=int, default=8081)

    parser.add_argument("--buffer-size", type=int, default=4096)

    parser.add_argument("--output-dir", default="data/output")
    parser.add_argument("--csv-path", default="data/results/http_dns_results.csv")

    args = parser.parse_args()

    run_web_client(args)


if __name__ == "__main__":
    main()
