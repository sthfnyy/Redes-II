# app/utils/auth.py

#Importa a biblioteca padrão do Python usada para gerar hashes, como SHA-256.
import hashlib


MATRICULA = "20189053789"
NOME = "Sthefany_Moura_Godinho"


def get_auth_hash():
    value = MATRICULA + NOME
    return hashlib.sha256(value.encode()).hexdigest()
