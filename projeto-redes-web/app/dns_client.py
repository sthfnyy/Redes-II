# app/dns_client.py

import argparse
import socket
import time
import uuid

from app.protocols.dns_message import build_query, parse_response


def resolve_name(
    dns_host: str,
    dns_port: int,
    name: str,
    timeout: float = 1.0,
    retries: int = 3,
):
    query_id = str(uuid.uuid4())[:8]
    query = build_query(query_id=query_id, name=name)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(timeout)

    start_time = time.perf_counter()

    for attempt in range(1, retries + 1):
        try:
            print(
                f"[DNS CLIENT] Tentativa {attempt}/{retries}: "
                f"resolvendo {name} em {dns_host}:{dns_port}"
            )

            sock.sendto(query, (dns_host, dns_port))

            response_data, _ = sock.recvfrom(1024)
            response = parse_response(response_data)

            elapsed_ms = (time.perf_counter() - start_time) * 1000

            if response.query_id != query_id:
                print("[DNS CLIENT] Resposta com ID diferente. Ignorando.")
                continue

            if response.status == "OK" and response.ip:
                print(f"[DNS CLIENT] Resolvido: {response.name} -> {response.ip}")
                print(f"[DNS CLIENT] Tempo DNS: {elapsed_ms:.3f} ms")
                print(f"[DNS CLIENT] Tentativas: {attempt}")

                return {
                    "success": True,
                    "name": response.name,
                    "ip": response.ip,
                    "dns_time_ms": elapsed_ms,
                    "dns_attempts": attempt,
                }

            print(f"[DNS CLIENT] Nome não encontrado: {name}")

            return {
                "success": False,
                "name": name,
                "ip": "",
                "dns_time_ms": elapsed_ms,
                "dns_attempts": attempt,
            }

        except socket.timeout:
            print(f"[DNS CLIENT] Timeout na tentativa {attempt}")

    elapsed_ms = (time.perf_counter() - start_time) * 1000

    return {
        "success": False,
        "name": name,
        "ip": "",
        "dns_time_ms": elapsed_ms,
        "dns_attempts": retries,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Cliente DNS simplificado via UDP."
    )

    parser.add_argument("--dns-host", default="127.0.0.1")
    parser.add_argument("--dns-port", type=int, default=5353)
    parser.add_argument("--name", default="www.sthefany.local")
    parser.add_argument("--timeout", type=float, default=1.0)
    parser.add_argument("--retries", type=int, default=3)

    args = parser.parse_args()

    result = resolve_name(
        dns_host=args.dns_host,
        dns_port=args.dns_port,
        name=args.name,
        timeout=args.timeout,
        retries=args.retries,
    )

    if result["success"]:
        print("[DNS CLIENT] Consulta finalizada com sucesso.")
    else:
        print("[DNS CLIENT] Falha na resolução DNS.")


if __name__ == "__main__":
    main()
