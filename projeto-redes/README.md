# Redes-II

#Arquitetura Inicial do projeto

projeto-redes/
│
├── app/
│   ├── client.py
│   ├── server.py
│   ├── protocols/
│   │   ├── tcp_transfer.py
│   │   ├── rudp_transfer.py
│   │   └── packet.py
│   │
│   ├── utils/
│   │   ├── auth.py
│   │   ├── checksum.py
│   │   ├── logger.py
│   │   └── file_utils.py
│   │
│   └── config.py
│
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
│
├── scripts/
│   ├── apply_tc.sh
│   ├── clear_tc.sh
│   ├── run_tcp_test.sh
│   ├── run_rudp_test.sh
│   └── run_all_tests.sh
│
├── data/
│   ├── input/
│   │   └── arquivo_teste.bin
│   ├── received/
│   ├── logs/
│   │   └── results.csv
│   └── pcaps/
│
├── analysis/
│   └── analyze.py
│
└── README.md
