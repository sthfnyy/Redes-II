# Redes-II — TCP vs R-UDP

## 1. Descrição

Este projeto implementa um sistema cliente/servidor em Python para transferência de arquivos em dois modos:

- TCP nativo;
- R-UDP, isto é, UDP com uma camada de confiabilidade implementada na aplicação.

O objetivo é comparar desempenho e confiabilidade dos dois protocolos sob diferentes condições de rede.

## 2. Objetivo do projeto

O projeto foi desenvolvido para a Segunda Avaliação de Redes de Computadores II, cujo tema é a análise de desempenho e confiabilidade em camadas de transporte.

A comparação considera:

- tempo de transferência;
- throughput;
- retransmissões;
- número de pacotes enviados;
- ACKs recebidos;
- capturas de rede com TCPDump/Wireshark.

## 3. Arquitetura

O projeto possui dois programas principais:

- `app/server.py`: inicia o servidor TCP ou R-UDP;
- `app/client.py`: envia o arquivo usando TCP ou R-UDP.

A implementação dos protocolos está em:

- `app/protocols/tcp_transfer.py`;
- `app/protocols/rudp_gbn.py`.

O protocolo R-UDP usa Go-Back-N com:

- número de sequência;
- ACK cumulativo;
- janela deslizante;
- timeout;
- retransmissão;
- checksum SHA-256 por bloco;
- campo `X-Custom-Auth`.

## 4. Configurações principais

As configurações estão no arquivo `app/config.py`:

- `CHUNK_SIZE = 1024`;
- `WINDOW_SIZE = 8`;
- `TIMEOUT = 1.0`;
- `TCP_PORT = 5000`;
- `RUDP_PORT = 5001`.

## 5. Cenários de teste

Os cenários são aplicados com `tc qdisc`:

| Cenário | Perda | Delay |
|---|---:|---:|
| A | 0% | 10 ms |
| B | 5% | 50 ms |
| C | 10% | 100 ms |

Script usado:

```bash
./scripts/apply_tc.sh A
./scripts/apply_tc.sh B
./scripts/apply_tc.sh C