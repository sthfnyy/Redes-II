# Redes II — Mini Web HTTP sobre TCP/R-UDP com DNS Local

## 1. Descrição

Este projeto implementa uma arquitetura simplificada da Internet composta por:

* um servidor DNS local simplificado sobre UDP nativo;
* um miniservidor Web HTTP/1.1 simplificado;
* um cliente Web que primeiro resolve o nome via DNS e depois realiza uma requisição HTTP;
* dois modos de transporte para o HTTP:

  * TCP nativo;
  * R-UDP, isto é, UDP com confiabilidade implementada na aplicação.

O objetivo é comparar o comportamento do carregamento de arquivos HTTP sobre TCP e sobre R-UDP em diferentes condições de rede.

O fluxo principal do sistema é:

```text
web_client -> dns_server -> web_client -> web_server
```

Em outras palavras:

```text
1. O cliente consulta o DNS local.
2. O DNS retorna o IP do servidor Web.
3. O cliente envia uma requisição HTTP GET.
4. O servidor Web responde com HTTP/1.1 200 OK ou 404 Not Found.
5. O cliente salva o arquivo recebido e registra métricas no CSV.
```

---

## 2. Objetivo do projeto

O projeto foi desenvolvido para o Trabalho Final de Redes de Computadores II.

A proposta é evoluir a implementação anterior de TCP vs R-UDP para uma arquitetura mais próxima da pilha da Internet, incluindo:

* resolução de nomes local;
* protocolo de aplicação HTTP/1.1 simplificado;
* transporte via TCP nativo;
* transporte via R-UDP com Go-Back-N;
* execução em containers Docker;
* aplicação de perda e atraso com `tc netem`;
* coleta de métricas e geração de resultados para análise.

---

## 3. Arquitetura Docker

A aplicação utiliza três containers principais:

| Container          | Função                            | IP           |
| ------------------ | --------------------------------- | ------------ |
| `redes_dns`        | Servidor DNS simplificado         | `172.28.0.2` |
| `redes_web_server` | Servidor Web HTTP TCP/R-UDP       | `172.28.0.3` |
| `redes_web_client` | Cliente Web e execução dos testes | `172.28.0.4` |

As portas utilizadas são:

| Serviço        | Protocolo  |  Porta |
| -------------- | ---------- | -----: |
| DNS local      | UDP nativo | `5300` |
| HTTP via TCP   | TCP        | `8080` |
| HTTP via R-UDP | UDP/R-UDP  | `8081` |

---

## 4. Estrutura do projeto

```text
.
├── app/
│   ├── config.py
│   ├── dns_client.py
│   ├── dns_server.py
│   ├── web_client.py
│   ├── web_server.py
│   ├── protocols/
│   │   ├── dns_message.py
│   │   ├── http_parser.py
│   │   ├── packet.py
│   │   └── rudp_gbn.py
│   ├── utils/
│   │   ├── auth.py
│   │   ├── checksum.py
│   │   └── logger.py
│   └── www/
│       ├── index.html
│       ├── arquivo_100kb.bin
│       ├── arquivo_1mb.bin
│       └── arquivo_10mb.bin
├── data/
│   ├── output/
│   └── results/
├── dns/
│   └── hosts.txt
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
├── scripts/
│   ├── apply_tc.sh
│   ├── clear_tc.sh
│   ├── run_http_dns_tests.sh
│   ├── run_http_dns_tests_single_scenario.sh
│   └── run_full_experiment_host.sh
└── README.md
```

---

## 5. Mini-DNS local

O DNS simplificado usa UDP nativo.

O arquivo de registros está em:

```text
dns/hosts.txt
```

Exemplo:

```text
www.sthefany.local 172.28.0.3
static.sthefany.local 172.28.0.3
```

Formato simplificado da consulta DNS:

```text
ID:<id>
TYPE:A
NAME:<nome>
```

Formato simplificado da resposta DNS:

```text
ID:<id>
STATUS:OK
NAME:<nome>
IP:<ip>
```

O cliente não acessa o servidor Web diretamente por IP. Ele primeiro consulta o DNS e usa o IP retornado.

---

## 6. HTTP/1.1 simplificado

O servidor Web aceita requisições HTTP GET no formato:

```http
GET /arquivo_100kb.bin HTTP/1.1
Host: www.sthefany.local
User-Agent: MiniWebClient/1.0
X-Custom-Auth: <hash>
Connection: close
```

As respostas implementadas incluem:

```http
HTTP/1.1 200 OK
```

e:

```http
HTTP/1.1 404 Not Found
```

Os cabeçalhos principais são:

* `Content-Type`;
* `Content-Length`;
* `X-Custom-Auth`;
* `Connection`.

Os arquivos servidos ficam em:

```text
app/www/
```

---

## 7. R-UDP com Go-Back-N

O modo R-UDP implementa uma camada de confiabilidade sobre UDP.

A implementação está em:

```text
app/protocols/rudp_gbn.py
```

O protocolo utiliza:

* pacotes `DATA`;
* número de sequência;
* ACK cumulativo;
* janela deslizante;
* timeout;
* retransmissão;
* checksum SHA-256 por bloco;
* autenticação via `X-Custom-Auth`;
* pacotes `FIN` e `FIN-ACK`;
* estratégia Go-Back-N.

As configurações principais estão em:

```text
app/config.py
```

Valores utilizados:

```python
CHUNK_SIZE = 1024
WINDOW_SIZE = 8
TIMEOUT = 1.0
MAX_PACKET_SIZE = 2048
```

---

## 8. Cenários de rede

Os cenários são aplicados com `tc netem` na interface `eth0` do container `redes_web_server`.

| Cenário | Perda |  Delay |
| ------- | ----: | -----: |
| A       |    0% |  10 ms |
| B       |    5% |  50 ms |
| C       |   10% | 100 ms |

Aplicar manualmente um cenário:

```bash
docker exec redes_web_server bash scripts/apply_tc.sh A eth0
docker exec redes_web_server bash scripts/apply_tc.sh B eth0
docker exec redes_web_server bash scripts/apply_tc.sh C eth0
```

Limpar regras:

```bash
docker exec redes_web_server bash scripts/clear_tc.sh eth0
```

---

## 9. Como executar o projeto

### 9.1 Subir os containers

Na raiz do projeto:

```bash
docker compose -f docker/docker-compose.yml up -d --build
```

Verificar containers:

```bash
docker ps --format "table {{.Names}}\t{{.ID}}\t{{.Status}}"
```

---

### 9.2 Iniciar o DNS

```bash
docker exec -d redes_dns python3 -m app.dns_server \
  --host 0.0.0.0 \
  --port 5300 \
  --hosts-file dns/hosts.txt
```

Testar DNS:

```bash
docker exec -it redes_web_client python3 -m app.dns_client \
  --dns-host 172.28.0.2 \
  --dns-port 5300 \
  --name www.sthefany.local
```

---

### 9.3 Iniciar o servidor Web TCP

```bash
docker exec -d redes_web_server python3 -m app.web_server \
  --mode tcp \
  --host 0.0.0.0 \
  --port 8080 \
  --www-dir app/www
```

---

### 9.4 Iniciar o servidor Web R-UDP

```bash
docker exec -d redes_web_server python3 -m app.web_server \
  --mode rudp \
  --host 0.0.0.0 \
  --port 8081 \
  --www-dir app/www
```

Verificar processos:

```bash
docker exec redes_dns pgrep -af "dns_server"
docker exec redes_web_server pgrep -af "web_server"
```

---

## 10. Executar cliente manualmente

### 10.1 HTTP via TCP

```bash
docker exec -it redes_web_client python3 -m app.web_client \
  --protocol tcp \
  --scenario A \
  --run 1 \
  --dns-host 172.28.0.2 \
  --dns-port 5300 \
  --host-name www.sthefany.local \
  --path /arquivo_100kb.bin \
  --tcp-port 8080
```

### 10.2 HTTP via R-UDP

```bash
docker exec -it redes_web_client python3 -m app.web_client \
  --protocol rudp \
  --scenario A \
  --run 1 \
  --dns-host 172.28.0.2 \
  --dns-port 5300 \
  --host-name www.sthefany.local \
  --path /arquivo_100kb.bin \
  --rudp-port 8081
```

---

## 11. Executar experimento completo

O script principal do experimento é:

```text
scripts/run_full_experiment_host.sh
```

Ele deve ser executado no host, ou seja, fora dos containers.

Executar:

```bash
./scripts/run_full_experiment_host.sh
```

Esse script:

1. limpa resultados antigos;
2. reinicia o DNS;
3. reinicia os servidores Web TCP e R-UDP;
4. aplica os cenários A, B e C com `tc`;
5. executa os testes no container cliente;
6. salva os resultados em CSV.

O número de repetições é controlado em:

```text
scripts/run_http_dns_tests_single_scenario.sh
```

Campo:

```bash
REPETITIONS=10
```

Para teste rápido, usar:

```bash
REPETITIONS=1
```

Para experimento completo, usar:

```bash
REPETITIONS=10
```

---

## 12. Resultados gerados

Os arquivos baixados pelo cliente são salvos em:

```text
data/output/
```

O CSV com as métricas é salvo em:

```text
data/results/http_dns_results.csv
```

Campos principais do CSV:

| Campo                  | Descrição                           |
| ---------------------- | ----------------------------------- |
| `timestamp`            | data/hora da execução               |
| `protocol`             | TCP ou RUDP                         |
| `scenario`             | cenário A, B ou C                   |
| `file_name`            | arquivo solicitado                  |
| `file_size_bytes`      | tamanho do corpo HTTP               |
| `run`                  | número da execução                  |
| `dns_time_ms`          | tempo da resolução DNS              |
| `dns_attempts`         | tentativas DNS                      |
| `http_time_ms`         | tempo da transferência HTTP         |
| `total_time_ms`        | tempo total com DNS                 |
| `throughput_mbps`      | taxa de transferência total         |
| `status_code`          | status HTTP                         |
| `http_header_bytes`    | tamanho do cabeçalho HTTP           |
| `http_body_bytes`      | tamanho do corpo HTTP               |
| `response_total_bytes` | tamanho total da resposta HTTP      |
| `retransmissions`      | retransmissões observadas no R-UDP  |
| `packets_sent`         | pacotes de dados recebidos no R-UDP |
| `acks_received`        | ACKs enviados/recebidos no R-UDP    |
| `success`              | indica sucesso ou falha             |

---

## 13. Verificações úteis

Contar linhas do CSV:

```bash
wc -l data/results/http_dns_results.csv
```

Verificar falhas:

```bash
grep ",False" data/results/http_dns_results.csv
```

Para experimento completo com 10 repetições, o esperado é:

```text
181 data/results/http_dns_results.csv
```

pois são:

```text
180 execuções + 1 cabeçalho
```

---

## 14. Captura de pacotes

Para validar no Wireshark/TCPDump, recomenda-se capturar exemplos menores, como `/index.html` ou `/arquivo_100kb.bin`.

Exemplo de captura no cliente:

```bash
docker exec -it redes_web_client tcpdump -i eth0 -w data/results/captura_http_dns.pcap
```

Em outro terminal, executar uma requisição TCP ou R-UDP.

Depois copiar o arquivo, se necessário:

```bash
docker cp redes_web_client:/workspace/data/results/captura_http_dns.pcap ./data/results/
```

As capturas devem evidenciar:

```text
DNS UDP -> resposta DNS -> HTTP TCP ou HTTP R-UDP
```

---

## 15. Observações sobre desempenho

Nos cenários com perda e atraso, especialmente o cenário C, o R-UDP com Go-Back-N pode apresentar tempo elevado em arquivos grandes.

Isso ocorre porque, quando um pacote é perdido, os pacotes seguintes podem chegar fora de ordem. O receptor reenvia o último ACK cumulativo válido, e o transmissor retransmite a janela a partir do pacote perdido.

Esse comportamento é esperado no Go-Back-N e faz parte da análise de desempenho do trabalho.

---

## 16. Encerrar ambiente

Limpar regras de rede:

```bash
docker exec redes_web_server bash scripts/clear_tc.sh eth0
```

Parar containers:

```bash
docker compose -f docker/docker-compose.yml down
```
