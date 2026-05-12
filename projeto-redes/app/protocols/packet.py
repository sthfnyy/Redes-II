# app/protocols/packet.py

HEADER_SEPARATOR = b"\n\n"


def build_packet(headers, payload=b""):
    """
    Monta um pacote com cabeçalho textual e payload binário.

    Formato:
        CHAVE:VALOR
        CHAVE:VALOR

        payload
    """

    header_text = ""

    for key, value in headers.items():
        header_text += f"{key}:{value}\n"

    return header_text.encode("utf-8") + b"\n" + payload


def parse_packet(packet):
    """
    Separa um pacote recebido em duas partes:
    - headers: dicionário com os campos do cabeçalho;
    - payload: bytes do arquivo.
    """

    if HEADER_SEPARATOR not in packet:
        raise ValueError("Pacote inválido: separador de cabeçalho não encontrado")

    header_raw, payload = packet.split(HEADER_SEPARATOR, 1)
    header_text = header_raw.decode("utf-8", errors="replace")

    headers = {}

    for line in header_text.splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            headers[key] = value

    return headers, payload