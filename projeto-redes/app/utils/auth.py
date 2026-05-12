# app/utils/auth.py

#Importa a biblioteca padrão do Python usada para gerar hashes, como SHA-256.
import hashlib


MATRICULA = "2023123456" #no teste verificar se tem que ser o meu mesmo
NOME = "Morgana_Moura_Gomes"


def get_auth_hash():
    value = MATRICULA + NOME
    return hashlib.sha256(value.encode()).hexdigest()
    #
    """
    Gera o hash SHA-256 exigido no cabeçalho X-Custom-Auth.

    O valor usado é:
        matrícula + nome
    """