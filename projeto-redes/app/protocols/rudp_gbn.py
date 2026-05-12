# app/protocols/rudp_gbn.py

import os
import socket
import time

from app.config import (
    AUTH_HEADER,
    CHUNK_SIZE,
    MAX_PACKET_SIZE,
    TIMEOUT,
    WINDOW_SIZE,
)

from app.protocols.packet import build_packet, parse_packet
from app.utils.auth import get_auth_hash
from app.utils.checksum import sha256_bytes


def create_data_packet(seq, chunk, auth_hash):
    """
    Cria um pacote DATA do protocolo R-UDP.

    Cada pacote contém:
    - X-Custom-Auth;
    - TYPE;
    - número de sequência;
    - tamanho do bloco;
    - checksum SHA-256 do bloco;
    - payload com os bytes do arquivo.
    """

    headers = {
        AUTH_HEADER: auth_hash,
        "TYPE": "DATA",
        "SEQ": seq,
        "SIZE": len(chunk),
        "CHECKSUM": sha256_bytes(chunk),
    }

    return build_packet(headers, chunk)


def create_ack_packet(ack_number, auth_hash):
    """
    Cria um pacote ACK cumulativo.

    ACK:N significa:
    recebi corretamente todos os pacotes até N.
    """

    headers = {
        AUTH_HEADER: auth_hash,
        "TYPE": "ACK",
        "ACK": ack_number,
    }

    return build_packet(headers)


def create_fin_packet(seq, auth_hash):
    """
    Cria pacote FIN para indicar fim da transmissão.
    """

    headers = {
        AUTH_HEADER: auth_hash,
        "TYPE": "FIN",
        "SEQ": seq,
    }

    return build_packet(headers)


def create_fin_ack_packet(ack_number, auth_hash):
    """
    Cria pacote FIN-ACK para confirmar o fim da transmissão.
    """

    headers = {
        AUTH_HEADER: auth_hash,
        "TYPE": "FIN-ACK",
        "ACK": ack_number,
    }

    return build_packet(headers)


def load_file_packets(file_path, auth_hash):
    """
    Lê o arquivo e transforma cada bloco em um pacote DATA.

    Retorna uma lista de pacotes já prontos para envio.
    """

    packets = []
    seq = 0

    with open(file_path, "rb") as file:
        while True:
            chunk = file.read(CHUNK_SIZE)

            if not chunk:
                break

            packet = create_data_packet(seq, chunk, auth_hash)
            packets.append(packet)
            seq += 1

    return packets


def send_file_rudp_gbn(host, port, file_path):
    """
    Envia arquivo usando R-UDP com Go-Back-N.

    Fluxo:
    1. Divide arquivo em pacotes DATA.
    2. Envia até WINDOW_SIZE pacotes por janela.
    3. Recebe ACK cumulativo.
    4. Se ACK avança, move a base da janela.
    5. Se timeout acontece, retransmite toda a janela não confirmada.
    6. Ao final, envia FIN e aguarda FIN-ACK.
    """

    auth_hash = get_auth_hash()
    packets = load_file_packets(file_path, auth_hash)

    total_packets = len(packets)

    base = 0
    next_seq = 0

    packets_sent = 0
    retransmissions = 0
    acks_received = 0

    timer_start = None

    print(f"[RUDP-GBN] Total de pacotes: {total_packets}")
    print(f"[RUDP-GBN] Janela: {WINDOW_SIZE}")
    print(f"[RUDP-GBN] Timeout: {TIMEOUT}s")

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.settimeout(0.1)

        while base < total_packets:
            while next_seq < base + WINDOW_SIZE and next_seq < total_packets:
                sock.sendto(packets[next_seq], (host, port))
                packets_sent += 1

                print(f"[RUDP-GBN] Enviado DATA seq={next_seq}")

                if base == next_seq:
                    timer_start = time.time()

                next_seq += 1

            try:
                response, _ = sock.recvfrom(MAX_PACKET_SIZE)
                headers, _ = parse_packet(response)

                if headers.get(AUTH_HEADER) != auth_hash:
                    print("[RUDP-GBN] ACK ignorado: X-Custom-Auth inválido")
                    continue

                if headers.get("TYPE") == "ACK":
                    ack = int(headers.get("ACK"))
                    print(f"[RUDP-GBN] Recebido ACK={ack}")

                    if ack >= base:
                        base = ack + 1
                        acks_received += 1

                        if base == next_seq:
                            timer_start = None
                        else:
                            timer_start = time.time()

            except socket.timeout:
                pass

            if timer_start is not None and time.time() - timer_start >= TIMEOUT:
                print(f"[RUDP-GBN] Timeout. Retransmitindo de seq={base} até seq={next_seq - 1}")

                for seq in range(base, next_seq):
                    sock.sendto(packets[seq], (host, port))
                    packets_sent += 1
                    retransmissions += 1

                    print(f"[RUDP-GBN] Retransmitido DATA seq={seq}")

                timer_start = time.time()

        send_fin(sock, host, port, total_packets, auth_hash)

    return {
        "packets_sent": packets_sent,
        "acks_received": acks_received,
        "retransmissions": retransmissions,
        "total_packets": total_packets,
    }


def send_fin(sock, host, port, seq, auth_hash):
    """
    Envia FIN até receber FIN-ACK.

    Isso garante que o servidor saiba que o arquivo acabou.
    """

    fin_packet = create_fin_packet(seq, auth_hash)

    while True:
        sock.sendto(fin_packet, (host, port))
        print("[RUDP-GBN] Enviado FIN")

        try:
            response, _ = sock.recvfrom(MAX_PACKET_SIZE)
            headers, _ = parse_packet(response)

            if headers.get(AUTH_HEADER) != auth_hash:
                continue

            if headers.get("TYPE") == "FIN-ACK":
                print("[RUDP-GBN] Recebido FIN-ACK")
                break

        except socket.timeout:
            print("[RUDP-GBN] Timeout no FIN. Retransmitindo FIN.")


def receive_file_rudp_gbn(host, port, output_path):
    """
    Recebe arquivo usando R-UDP com Go-Back-N.

    O servidor:
    - espera pacotes em ordem;
    - valida X-Custom-Auth;
    - valida checksum;
    - grava somente o pacote esperado;
    - descarta pacotes fora de ordem;
    - envia ACK cumulativo.
    """

    auth_hash = get_auth_hash()

    expected_seq = 0
    last_ack = -1

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.bind((host, port))

        print(f"[RUDP-GBN] Servidor escutando em {host}:{port}")
        print(f"[RUDP-GBN] Aguardando pacotes...")

        with open(output_path, "wb") as file:
            while True:
                packet, client_addr = sock.recvfrom(MAX_PACKET_SIZE)

                try:
                    headers, payload = parse_packet(packet)
                except ValueError:
                    print("[RUDP-GBN] Pacote inválido ignorado")
                    continue

                if headers.get(AUTH_HEADER) != auth_hash:
                    print("[RUDP-GBN] Pacote ignorado: X-Custom-Auth inválido")
                    continue

                packet_type = headers.get("TYPE")

                if packet_type == "DATA":
                    seq = int(headers.get("SEQ"))
                    received_checksum = headers.get("CHECKSUM")
                    calculated_checksum = sha256_bytes(payload)

                    if received_checksum != calculated_checksum:
                        print(f"[RUDP-GBN] Checksum inválido seq={seq}")
                        ack_packet = create_ack_packet(last_ack, auth_hash)
                        sock.sendto(ack_packet, client_addr)
                        continue

                    if seq == expected_seq:
                        file.write(payload)
                        file.flush()

                        last_ack = seq
                        expected_seq += 1

                        print(f"[RUDP-GBN] Recebido em ordem DATA seq={seq}. ACK={last_ack}")

                    else:
                        print(
                            f"[RUDP-GBN] Fora de ordem DATA seq={seq}. "
                            f"Esperado={expected_seq}. Reenviando ACK={last_ack}"
                        )

                    ack_packet = create_ack_packet(last_ack, auth_hash)
                    sock.sendto(ack_packet, client_addr)

                elif packet_type == "FIN":
                    fin_seq = int(headers.get("SEQ"))

                    fin_ack_packet = create_fin_ack_packet(fin_seq, auth_hash)
                    sock.sendto(fin_ack_packet, client_addr)

                    print("[RUDP-GBN] Recebido FIN")
                    print("[RUDP-GBN] Enviado FIN-ACK")
                    print("[RUDP-GBN] Transferência finalizada")
                    break