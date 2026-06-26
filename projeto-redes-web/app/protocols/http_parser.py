# app/protocols/http_parser.py

from pathlib import Path
from mimetypes import guess_type

from app.utils.auth import get_auth_hash

HTTP_SEPARATOR = b"\r\n\r\n"


def parse_http_request(request_bytes: bytes) -> dict:
    """
    Faz o parse de uma requisição HTTP/1.1 simplificada.

    Exemplo esperado:

    GET /index.html HTTP/1.1
    Host: www.sthefany.local
    X-Custom-Auth: <hash>
    Connection: close
    """

    text = request_bytes.decode("utf-8", errors="replace")
    lines = text.splitlines()

    if not lines:
        raise ValueError("Requisição HTTP vazia.")

    request_line = lines[0].strip()
    parts = request_line.split()

    if len(parts) != 3:
        raise ValueError("Linha de requisição HTTP inválida.")

    method, path, version = parts

    headers = {}

    for line in lines[1:]:
        if not line.strip():
            break

        if ":" in line:
            key, value = line.split(":", 1)
            headers[key.strip()] = value.strip()

    return {
        "method": method,
        "path": path,
        "version": version,
        "headers": headers,
    }


def build_http_get_request(host: str, path: str) -> bytes:
    """
    Monta uma requisição GET HTTP/1.1 simplificada.
    """

    auth_hash = get_auth_hash()

    request = (
        f"GET {path} HTTP/1.1\r\n"
        f"Host: {host}\r\n"
        f"User-Agent: MiniWebClient/1.0\r\n"
        f"X-Custom-Auth: {auth_hash}\r\n"
        f"Connection: close\r\n"
        f"\r\n"
    )

    return request.encode("utf-8")


def get_content_type(file_path: Path) -> str:
    """
    Descobre o Content-Type com base na extensão do arquivo.
    """

    content_type, _ = guess_type(str(file_path))

    if content_type:
        return content_type

    return "application/octet-stream"


def build_http_response(
    status_code: int,
    reason: str,
    body: bytes,
    content_type: str,
) -> bytes:
    """
    Monta uma resposta HTTP/1.1 simplificada.
    """

    auth_hash = get_auth_hash()

    header = (
        f"HTTP/1.1 {status_code} {reason}\r\n"
        f"Content-Type: {content_type}\r\n"
        f"Content-Length: {len(body)}\r\n"
        f"X-Custom-Auth: {auth_hash}\r\n"
        f"Connection: close\r\n"
        f"\r\n"
    )

    return header.encode("utf-8") + body


def split_http_response(response_bytes: bytes) -> tuple[bytes, bytes]:
    """
    Separa cabeçalho e corpo da resposta HTTP.
    """

    if HTTP_SEPARATOR not in response_bytes:
        return response_bytes, b""

    header, body = response_bytes.split(HTTP_SEPARATOR, 1)

    return header + HTTP_SEPARATOR, body


def parse_status_code(response_header: bytes) -> int:
    """
    Extrai o status code da resposta HTTP.
    """

    text = response_header.decode("utf-8", errors="replace")
    first_line = text.splitlines()[0]

    parts = first_line.split()

    if len(parts) < 2:
        return 0

    try:
        return int(parts[1])
    except ValueError:
        return 0
