# app/utils/checksum.py

#Importa a biblioteca de hash.
import hashlib


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()

    """
    Calcula o SHA-256 de um conjunto de bytes.

    Será usado para validar a integridade de cada bloco enviado.
    """