# app/server.py

import argparse

from app.config import TCP_PORT, RUDP_PORT
from app.protocols.tcp_transfer import receive_file_tcp

from app.protocols.rudp_gbn import receive_file_rudp_gbn

def main():
    """
    Programa principal do servidor.

    Ele recebe argumentos pela linha de comando e inicia o servidor
    no protocolo escolhido.
    """

    parser = argparse.ArgumentParser(
        description="Servidor de transferência de arquivos TCP/R-UDP"
    )

    parser.add_argument(
        "--protocol",
        choices=["tcp", "rudp"],
        required=True,
        help="Protocolo usado na transferência: tcp ou rudp",
    )

    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Endereço IP em que o servidor vai escutar",
    )

    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="Porta em que o servidor vai escutar",
    )

    parser.add_argument(
        "--output",
        required=True,
        help="Caminho onde o arquivo recebido será salvo",
    )

    args = parser.parse_args()

    if args.port is None:
        if args.protocol == "tcp":
            args.port = TCP_PORT
        else:
            args.port = RUDP_PORT

    if args.protocol == "tcp":
        receive_file_tcp(args.host, args.port, args.output)

    elif args.protocol == "rudp":
        receive_file_rudp_gbn(args.host, args.port, args.output)


if __name__ == "__main__":
    main()

    
# - escutar uma porta;
# - receber arquivo via TCP ou R-UDP;
# - salvar o arquivo recebido em data/received/;
# - validar o X-Custom-Auth no modo R-UDP.