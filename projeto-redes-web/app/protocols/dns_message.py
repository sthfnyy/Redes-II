# app/protocols/dns_message.py

"""
Mensagens DNS simplificadas para o trabalho final.

Formato da consulta:

ID:1
TYPE:A
NAME:www.sthefany.local

Formato da resposta:

ID:1
STATUS:OK
NAME:www.sthefany.local
IP:172.28.0.3
"""

from dataclasses import dataclass


@dataclass
class DNSQuery:
    query_id: str
    query_type: str
    name: str


@dataclass
class DNSResponse:
    query_id: str
    status: str
    name: str
    ip: str


def build_query(query_id: str, name: str, query_type: str = "A") -> bytes:
    message = (
        f"ID:{query_id}\n"
        f"TYPE:{query_type}\n"
        f"NAME:{name}\n"
    )

    return message.encode("utf-8")


def parse_query(data: bytes) -> DNSQuery:
    text = data.decode("utf-8", errors="replace").strip()
    fields = {}

    for line in text.splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            fields[key.strip().upper()] = value.strip()

    query_id = fields.get("ID", "")
    query_type = fields.get("TYPE", "")
    name = fields.get("NAME", "")

    if not query_id or not query_type or not name:
        raise ValueError("Consulta DNS inválida.")

    return DNSQuery(
        query_id=query_id,
        query_type=query_type,
        name=name,
    )


def build_response(query_id: str, name: str, ip: str | None) -> bytes:
    if ip:
        status = "OK"
        ip_value = ip
    else:
        status = "NOT_FOUND"
        ip_value = ""

    message = (
        f"ID:{query_id}\n"
        f"STATUS:{status}\n"
        f"NAME:{name}\n"
        f"IP:{ip_value}\n"
    )

    return message.encode("utf-8")


def parse_response(data: bytes) -> DNSResponse:
    text = data.decode("utf-8", errors="replace").strip()
    fields = {}

    for line in text.splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            fields[key.strip().upper()] = value.strip()

    query_id = fields.get("ID", "")
    status = fields.get("STATUS", "")
    name = fields.get("NAME", "")
    ip = fields.get("IP", "")

    if not query_id or not status or not name:
        raise ValueError("Resposta DNS inválida.")

    return DNSResponse(
        query_id=query_id,
        status=status,
        name=name,
        ip=ip,
    )
