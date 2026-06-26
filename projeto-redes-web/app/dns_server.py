# app/dns_server.py

import argparse
import socket
from pathlib import Path

from app.protocols.dns_message import parse_query, build_response


def load_hosts(hosts_file: str) -> dict[str, str]:
    hosts = {}

    path = Path(hosts_file)

    if not path.exists():
        raise FileNotFoundError(f"Arquivo de hosts não encontrado: {hosts_file}")

    with path.open("r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()

            if not line or line.startswith("#"):
                continue

            parts = line.split()

            if len(parts) != 2:
                continue

            name, ip = parts
            hosts[name.strip()] = ip.strip()

    return hosts


def run_dns_server(host: str, port: int, hosts_file: str):
    hosts = load_hosts(hosts_file)

    print("[DNS] Servidor DNS iniciado")
    print(f"[DNS] Host: {host}")
    print(f"[DNS] Porta: {port}")
    print(f"[DNS] Arquivo de hosts: {hosts_file}")
    print(f"[DNS] Registros carregados: {hosts}")

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((host, port))

    while True:
        data, client_address = sock.recvfrom(1024)

        try:
            query = parse_query(data)

            print(
                f"[DNS] Consulta recebida de {client_address}: "
                f"ID={query.query_id} TYPE={query.query_type} NAME={query.name}"
            )

            if query.query_type.upper() != "A":
                ip = None
            else:
                ip = hosts.get(query.name)

            response = build_response(
                query_id=query.query_id,
                name=query.name,
                ip=ip,
            )

            sock.sendto(response, client_address)

            if ip:
                print(f"[DNS] Resposta enviada: {query.name} -> {ip}")
            else:
                print(f"[DNS] Nome não encontrado: {query.name}")

        except Exception as exc:
            print(f"[DNS] Erro ao processar consulta: {exc}")


def main():
    parser = argparse.ArgumentParser(
        description="Servidor DNS simplificado via UDP."
    )

    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=5353)
    parser.add_argument("--hosts-file", default="dns/hosts.txt")

    args = parser.parse_args()

    run_dns_server(
        host=args.host,
        port=args.port,
        hosts_file=args.hosts_file,
    )


if __name__ == "__main__":
    main()
