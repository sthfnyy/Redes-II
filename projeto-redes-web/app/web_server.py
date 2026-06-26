# app/web_server.py

import argparse
import socket
import time
from pathlib import Path

from app.protocols.http_parser import (
    parse_http_request,
    build_http_response,
    get_content_type,
)

from app.protocols.rudp_gbn import (
    receive_bytes_rudp_gbn,
    send_bytes_rudp_gbn,
)


def safe_resolve_path(www_dir: str, request_path: str) -> Path | None:
    """
    Resolve o caminho solicitado pelo GET de forma segura.

    Exemplo:
    /index.html -> app/www/index.html
    /           -> app/www/index.html
    """

    base_dir = Path(www_dir).resolve()

    if request_path == "/":
        request_path = "/index.html"

    # Remove a barra inicial para montar caminho relativo
    relative_path = request_path.lstrip("/")

    file_path = (base_dir / relative_path).resolve()

    # Evita acesso fora da pasta www com caminhos tipo ../../
    if not str(file_path).startswith(str(base_dir)):
        return None

    return file_path


def receive_http_request(conn: socket.socket, buffer_size: int = 4096) -> bytes:
    """
    Recebe a requisição HTTP até encontrar o fim do cabeçalho: \\r\\n\\r\\n.
    """

    data = b""

    while b"\r\n\r\n" not in data:
        chunk = conn.recv(buffer_size)

        if not chunk:
            break

        data += chunk

        # Segurança para não aceitar cabeçalho gigante
        if len(data) > 65536:
            break

    return data


def handle_tcp_client(conn: socket.socket, address, www_dir: str):
    print(f"[WEB TCP] Cliente conectado: {address}")

    try:
        request_bytes = receive_http_request(conn)
        request = parse_http_request(request_bytes)

        method = request["method"]
        path = request["path"]

        print(f"[WEB TCP] Requisição: {method} {path}")

        if method.upper() != "GET":
            body = b"<html><body><h1>405 Method Not Allowed</h1></body></html>"
            response = build_http_response(
                status_code=405,
                reason="Method Not Allowed",
                body=body,
                content_type="text/html",
            )
            conn.sendall(response)
            return

        file_path = safe_resolve_path(www_dir, path)

        if file_path is None or not file_path.exists() or not file_path.is_file():
            body = b"<html><body><h1>404 Not Found</h1></body></html>"
            response = build_http_response(
                status_code=404,
                reason="Not Found",
                body=body,
                content_type="text/html",
            )
            conn.sendall(response)

            print(f"[WEB TCP] 404 Not Found: {path}")
            return

        body = file_path.read_bytes()
        content_type = get_content_type(file_path)

        response = build_http_response(
            status_code=200,
            reason="OK",
            body=body,
            content_type=content_type,
        )

        conn.sendall(response)

        print(
            f"[WEB TCP] 200 OK: {path} "
            f"({len(body)} bytes, {content_type})"
        )

    except Exception as exc:
        print(f"[WEB TCP] Erro ao processar cliente {address}: {exc}")

        try:
            body = b"<html><body><h1>500 Internal Server Error</h1></body></html>"
            response = build_http_response(
                status_code=500,
                reason="Internal Server Error",
                body=body,
                content_type="text/html",
            )
            conn.sendall(response)
        except Exception:
            pass

    finally:
        conn.close()
        print(f"[WEB TCP] Conexão encerrada: {address}")


def run_tcp_web_server(host: str, port: int, www_dir: str):
    print("[WEB TCP] Servidor Web HTTP/1.1 simplificado iniciado")
    print(f"[WEB TCP] Host: {host}")
    print(f"[WEB TCP] Porta: {port}")
    print(f"[WEB TCP] Diretório WWW: {www_dir}")

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    sock.bind((host, port))
    sock.listen(10)

    print("[WEB TCP] Aguardando conexões...")

    while True:
        conn, address = sock.accept()
        handle_tcp_client(conn, address, www_dir)

def build_response_for_request(request_bytes: bytes, www_dir: str) -> tuple[bytes, int, str, int]:
    """
    Processa uma requisição HTTP em bytes e retorna:
    - resposta HTTP completa em bytes
    - status code
    - path solicitado
    - tamanho do corpo
    """

    request = parse_http_request(request_bytes)

    method = request["method"]
    path = request["path"]

    print(f"[WEB] Requisição: {method} {path}")

    if method.upper() != "GET":
        body = b"<html><body><h1>405 Method Not Allowed</h1></body></html>"
        response = build_http_response(
            status_code=405,
            reason="Method Not Allowed",
            body=body,
            content_type="text/html",
        )

        return response, 405, path, len(body)

    file_path = safe_resolve_path(www_dir, path)

    if file_path is None or not file_path.exists() or not file_path.is_file():
        body = b"<html><body><h1>404 Not Found</h1></body></html>"
        response = build_http_response(
            status_code=404,
            reason="Not Found",
            body=body,
            content_type="text/html",
        )

        print(f"[WEB] 404 Not Found: {path}")

        return response, 404, path, len(body)

    body = file_path.read_bytes()
    content_type = get_content_type(file_path)

    response = build_http_response(
        status_code=200,
        reason="OK",
        body=body,
        content_type=content_type,
    )

    print(
        f"[WEB] 200 OK: {path} "
        f"({len(body)} bytes, {content_type})"
    )

    return response, 200, path, len(body)


def run_rudp_web_server(host: str, port: int, www_dir: str):
    """
    Servidor Web HTTP/1.1 simplificado sobre R-UDP.
    """

    print("[WEB RUDP] Servidor Web HTTP/1.1 simplificado sobre R-UDP iniciado")
    print(f"[WEB RUDP] Host: {host}")
    print(f"[WEB RUDP] Porta: {port}")
    print(f"[WEB RUDP] Diretório WWW: {www_dir}")

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((host, port))

    print("[WEB RUDP] Aguardando requisições R-UDP...")

    while True:
        try:
            start_time = time.perf_counter()

            received = receive_bytes_rudp_gbn(sock)

            request_bytes = received["data"]
            client_address = received["client_address"]

            print(f"[WEB RUDP] Requisição recebida de {client_address}")

            response_bytes, status_code, path, body_size = build_response_for_request(
                request_bytes=request_bytes,
                www_dir=www_dir,
            )

            send_metrics = send_bytes_rudp_gbn(
                sock=sock,
                address=client_address,
                data=response_bytes,
            )

            elapsed_ms = (time.perf_counter() - start_time) * 1000

            print(
                f"[WEB RUDP] Resposta enviada para {client_address} "
                f"status={status_code} path={path} body={body_size} bytes "
                f"tempo={elapsed_ms:.3f} ms "
                f"retransmissions={send_metrics['retransmissions']}"
            )

        except Exception as exc:
            print(f"[WEB RUDP] Erro ao processar requisição: {exc}")


def main():
    parser = argparse.ArgumentParser(
        description="Mini servidor Web HTTP/1.1 simplificado."
    )

    parser.add_argument("--mode", choices=["tcp", "rudp"], default="tcp")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--www-dir", default="app/www")

    args = parser.parse_args()

    if args.mode == "tcp":
        run_tcp_web_server(
            host=args.host,
            port=args.port,
            www_dir=args.www_dir,
        )

    elif args.mode == "rudp":
        run_rudp_web_server(
            host=args.host,
            port=args.port,
            www_dir=args.www_dir,
        )


if __name__ == "__main__":
    main()