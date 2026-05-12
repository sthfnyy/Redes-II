# app/protocols/tcp_transfer.py

import os
import socket

from app.config import AUTH_HEADER, CHUNK_SIZE
from app.utils.auth import get_auth_hash


def build_tcp_header(file_path):
    """
    Monta o cabeçalho textual enviado antes dos bytes do arquivo.

    Esse cabeçalho informa:
    - hash de autenticação X-Custom-Auth;
    - nome do arquivo;
    - tamanho do arquivo em bytes.
    """

    file_name = os.path.basename(file_path)
    file_size = os.path.getsize(file_path)
    auth_hash = get_auth_hash()

    header = (
        f"{AUTH_HEADER}:{auth_hash}\n"
        f"FILENAME:{file_name}\n"
        f"FILESIZE:{file_size}\n"
        "\n"
    )

    return header.encode("utf-8")


def parse_tcp_header(header_text):
    """
    Converte o cabeçalho textual recebido em um dicionário Python.
    """

    headers = {}

    for line in header_text.splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            headers[key] = value

    return headers


def send_file_tcp(host, port, file_path):
    """
    Envia um arquivo usando socket TCP.

    Fluxo:
    1. Abre conexão TCP com o servidor.
    2. Envia cabeçalho textual.
    3. Envia o arquivo em blocos.
    4. Fecha a conexão.
    """

    packets_sent = 0

    header = build_tcp_header(file_path)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((host, port))

        sock.sendall(header)

        with open(file_path, "rb") as file:
            while True:
                chunk = file.read(CHUNK_SIZE)

                if not chunk:
                    break

                sock.sendall(chunk)
                packets_sent += 1

    return {
        "packets_sent": packets_sent,
        "acks_received": 0,
        "retransmissions": 0,
        "total_packets": packets_sent,
    }


def receive_file_tcp(host, port, output_path):
    """
    Recebe um arquivo usando socket TCP.

    Fluxo:
    1. Abre socket TCP no servidor.
    2. Aguarda conexão do cliente.
    3. Lê cabeçalho textual.
    4. Descobre o tamanho do arquivo.
    5. Recebe os bytes até completar o tamanho esperado.
    6. Salva o arquivo em output_path.
    """

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((host, port))
        server.listen(1)

        print(f"[TCP] Servidor escutando em {host}:{port}")

        conn, addr = server.accept()

        with conn:
            print(f"[TCP] Conexão recebida de {addr}")

            buffer = b""

            while b"\n\n" not in buffer:
                data = conn.recv(CHUNK_SIZE)

                if not data:
                    raise ConnectionError("Conexão encerrada antes do cabeçalho completo.")

                buffer += data

            header_raw, remaining_data = buffer.split(b"\n\n", 1)
            header_text = header_raw.decode("utf-8", errors="replace")
            headers = parse_tcp_header(header_text)

            auth_hash = get_auth_hash()

            if headers.get(AUTH_HEADER) != auth_hash:
                raise ValueError("X-Custom-Auth inválido no TCP.")

            file_size = int(headers["FILESIZE"])

            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            received_bytes = 0

            with open(output_path, "wb") as file:
                if remaining_data:
                    file.write(remaining_data)
                    received_bytes += len(remaining_data)

                while received_bytes < file_size:
                    data = conn.recv(CHUNK_SIZE)

                    if not data:
                        break

                    file.write(data)
                    received_bytes += len(data)

            print(f"[TCP] Arquivo recebido: {received_bytes} bytes")

            if received_bytes != file_size:
                raise ValueError(
                    f"Arquivo incompleto. Esperado={file_size}, recebido={received_bytes}"
                )