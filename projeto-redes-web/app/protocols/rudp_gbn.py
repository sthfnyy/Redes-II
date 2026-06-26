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
    headers = {
        AUTH_HEADER: auth_hash,
        "TYPE": "DATA",
        "SEQ": seq,
        "SIZE": len(chunk),
        "CHECKSUM": sha256_bytes(chunk),
    }

    return build_packet(headers, chunk)


def create_ack_packet(ack_number, auth_hash):
    headers = {
        AUTH_HEADER: auth_hash,
        "TYPE": "ACK",
        "ACK": ack_number,
    }

    return build_packet(headers)


def create_fin_packet(seq, auth_hash):
    headers = {
        AUTH_HEADER: auth_hash,
        "TYPE": "FIN",
        "SEQ": seq,
    }

    return build_packet(headers)


def create_fin_ack_packet(ack_number, auth_hash):
    headers = {
        AUTH_HEADER: auth_hash,
        "TYPE": "FIN-ACK",
        "ACK": ack_number,
    }

    return build_packet(headers)


def build_data_packets_from_bytes(data: bytes, auth_hash: str):
    packets = []
    seq = 0

    for start in range(0, len(data), CHUNK_SIZE):
        chunk = data[start:start + CHUNK_SIZE]
        packet = create_data_packet(seq, chunk, auth_hash)
        packets.append(packet)
        seq += 1

    return packets


def send_fin_to_address(sock, address, seq, auth_hash, max_attempts=20):
    fin_packet = create_fin_packet(seq, auth_hash)

    sock.settimeout(1.0)

    for attempt in range(1, max_attempts + 1):
        sock.sendto(fin_packet, address)

        print(f"[RUDP-GBN] Enviado FIN tentativa {attempt}/{max_attempts}")

        try:
            response, _ = sock.recvfrom(MAX_PACKET_SIZE)
            headers, _ = parse_packet(response)

            if headers.get(AUTH_HEADER) != auth_hash:
                continue

            if headers.get("TYPE") == "FIN-ACK":
                print("[RUDP-GBN] Recebido FIN-ACK")
                return True

        except socket.timeout:
            print("[RUDP-GBN] Timeout no FIN. Retransmitindo FIN.")

    raise TimeoutError("[RUDP-GBN] Falha ao finalizar: FIN-ACK não recebido.")


def send_bytes_rudp_gbn(sock, address, data: bytes):
    auth_hash = get_auth_hash()
    packets = build_data_packets_from_bytes(data, auth_hash)

    total_packets = len(packets)

    base = 0
    next_seq = 0

    packets_sent = 0
    retransmissions = 0
    acks_received = 0

    timer_start = None

    print(f"[RUDP-GBN] Enviando bytes: {len(data)} bytes")
    print(f"[RUDP-GBN] Total de pacotes: {total_packets}")
    print(f"[RUDP-GBN] Janela: {WINDOW_SIZE}")
    print(f"[RUDP-GBN] Timeout: {TIMEOUT}s")

    sock.settimeout(0.1)

    while base < total_packets:
        while next_seq < base + WINDOW_SIZE and next_seq < total_packets:
            sock.sendto(packets[next_seq], address)
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
            print(
                f"[RUDP-GBN] Timeout. Retransmitindo de seq={base} "
                f"até seq={next_seq - 1}"
            )

            for seq in range(base, next_seq):
                sock.sendto(packets[seq], address)
                packets_sent += 1
                retransmissions += 1

                print(f"[RUDP-GBN] Retransmitido DATA seq={seq}")

            timer_start = time.time()

    fin_seq = total_packets
    send_fin_to_address(sock, address, fin_seq, auth_hash)

    return {
        "packets_sent": packets_sent,
        "acks_received": acks_received,
        "retransmissions": retransmissions,
        "total_packets": total_packets,
    }

def receive_bytes_rudp_gbn(sock):
    auth_hash = get_auth_hash()

    expected_seq = 0
    last_ack = -1

    chunks = []

    packets_received = 0
    acks_sent = 0

    print("[RUDP-GBN] Aguardando mensagem R-UDP...")

    # Durante perda/delay, o receptor não deve morrer no primeiro timeout.
    # Ele continua aguardando retransmissões do Go-Back-N.
    sock.settimeout(5.0)

    while True:
        try:
            packet, client_addr = sock.recvfrom(MAX_PACKET_SIZE)
        except socket.timeout:
            print("[RUDP-GBN] Timeout aguardando pacote. Continuando espera...")
            continue

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
                acks_sent += 1
                continue

            if seq == expected_seq:
                chunks.append(payload)
                last_ack = seq
                expected_seq += 1
                packets_received += 1

                print(f"[RUDP-GBN] Recebido em ordem DATA seq={seq}. ACK={last_ack}")

            else:
                print(
                    f"[RUDP-GBN] Fora de ordem DATA seq={seq}. "
                    f"Esperado={expected_seq}. Reenviando ACK={last_ack}"
                )

            ack_packet = create_ack_packet(last_ack, auth_hash)
            sock.sendto(ack_packet, client_addr)
            acks_sent += 1

        elif packet_type == "FIN":
            fin_seq = int(headers.get("SEQ"))

            fin_ack_packet = create_fin_ack_packet(fin_seq, auth_hash)

            for _ in range(5):
                sock.sendto(fin_ack_packet, client_addr)

            print("[RUDP-GBN] Recebido FIN")
            print("[RUDP-GBN] Enviado FIN-ACK")
            print("[RUDP-GBN] Mensagem finalizada")

            data = b"".join(chunks)

            return {
                "data": data,
                "client_address": client_addr,
                "packets_received": packets_received,
                "acks_sent": acks_sent,
            }

def load_file_packets(file_path, auth_hash):
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


def send_fin(sock, host, port, seq, auth_hash):
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


def send_file_rudp_gbn(host, port, file_path):
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
                print(
                    f"[RUDP-GBN] Timeout. Retransmitindo de seq={base} "
                    f"até seq={next_seq - 1}"
                )

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


def receive_file_rudp_gbn(host, port, output_path):
    auth_hash = get_auth_hash()

    expected_seq = 0
    last_ack = -1

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.bind((host, port))

        print(f"[RUDP-GBN] Servidor escutando em {host}:{port}")
        print("[RUDP-GBN] Aguardando pacotes...")

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
