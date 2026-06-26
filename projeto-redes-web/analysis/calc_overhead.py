from app.protocols.rudp_gbn import create_data_packet, create_ack_packet, create_fin_packet
from app.utils.auth import get_auth_hash
from app.config import CHUNK_SIZE


def main():
    auth_hash = get_auth_hash()

    payload = b"A" * CHUNK_SIZE

    data_packet = create_data_packet(0, payload, auth_hash)
    ack_packet = create_ack_packet(0, auth_hash)
    fin_packet = create_fin_packet(0, auth_hash)

    data_overhead = len(data_packet) - len(payload)
    ack_overhead = len(ack_packet)
    fin_overhead = len(fin_packet)

    print("Overhead R-UDP")
    print("----------------")
    print(f"Payload DATA: {len(payload)} bytes")
    print(f"Pacote DATA total: {len(data_packet)} bytes")
    print(f"Overhead DATA: {data_overhead} bytes")
    print()
    print(f"Pacote ACK: {ack_overhead} bytes")
    print(f"Pacote FIN: {fin_overhead} bytes")


if __name__ == "__main__":
    main()