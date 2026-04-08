# Sistema IoT — Painel Operacional com Controle de Ambiente

Um sistema distribuído de IoT para monitoramento e controle de temperatura e umidade em tempo real, com interface interativa para operadores e automação inteligente de atuadores.

---

## 📋 Visão Geral

O projeto implementa uma arquitetura cliente-servidor com:

- **Servidor Central**: Orquestra sensores, atuadores e operadores via TCP/UDP
- **Sensores**: Enviam leituras periódicas de temperatura e umidade via UDP
- **Atuadores**: Ventilador e umidificador controlados via TCP com comando automático ou manual
- **Painel do Operador**: Interface interativa para visualizar status e enviar overrides manuais

### Características

- ✅ Comunicação em tempo real (TCP + UDP)
- ✅ Dashboard interativo com cores ANSI
- ✅ Controle automático baseado em limiares configuráveis
- ✅ Override manual por operadores (suspende automação)
- ✅ Log de eventos com timestamp (fuso horário Bahia)
- ✅ Reconexão automática em caso de falha
- ✅ Containerização com Docker/Docker Compose

---

## 🏗️ Arquitetura


SERVIDOR (TCP+UDP) 
- TCP 12345: Clientes (Operador, Atuadores) 
- UDP 12346: Sensor Temperatura 
- UDP 12347: Sensor Umidade 
- Gerencia: lógica de automação, overrides, abcast 


│ SENSORES │ │ ATUADORES  │ │ OPERADOR │
|    (UDP) │ │    (TCP)   │ │  (TCP)   │
│    Temp  │ │ Ventilador │ │ Dashboard│
|  Umidade │ │Umidificador│ │   Menu   │


---

## 🔧 Pré-requisitos

- Docker 20.10+
- Docker Compose 2.0+
- Terminal com suporte a ANSI colors (Linux/macOS ou Windows Terminal)

---

## 🚀 Como Executar

### 1️⃣ Servidor e Sensores (em segundo plano)

```bash
# Navegar para a pasta Server
cd Server
docker compose up -d

# Navegar para a pasta Sensors (em outro terminal)
cd ../Sensors
docker compose up -d

Confirmação esperada:
[+] Running 3/3
  ✔ Container iot_server      Started
  ✔ Container sensor-temp     Started
  ✔ Container sensor-umid     Started

2️⃣ Painel do Operador (modo interativo)
# Em outro terminal, navegar para Client
cd ../Client
docker compose run --rm operador

Você verá:

Banner inicial
Prompt para digitar seu nome
Menu com opções:
1: Enviar override (ligar/desligar atuadores manualmente)
2: Visualizar status do sistema (dashboard em tempo real)
3: Sair

3️⃣ Parar Sistema Completo
# Server
cd Server
docker compose down

# Sensors
cd ../Sensors
docker compose down

cd ../Client
docker compose down

📊 Protocolo de Comunicação
Mensagens TCP (Servidor ↔ Clientes)

Identificação (Cliente → Servidor):
{"tipo": "identificacao", "dispositivo": "operador|ventilador|umidificador"}

Confirmação (Servidor → Cliente):
{"tipo": "confirmacao", "mensagem": "Conectado como OPERADOR..."}

Comando (Servidor → Atuador):
{"tipo": "comando", "acao": "LIGAR_VENTILADOR|DESLIGAR_VENTILADOR|..."}

Status (Atuador → Servidor):
{"tipo": "status", "dispositivo": "ventilador", "estado": "LIGADO"}

Override (Operador → Servidor):
{"tipo": "override", "acao": "LIGAR_VENTILADOR", "operador": "João"}

Broadcast (Servidor → Operadores):
{"tipo": "sensor_update", "dispositivo": "temperatura", "valor": 28, "unidade": "°C"}
{"tipo": "atuador_update", "dispositivo": "ventilador", "estado": "LIGADO", "override": false, "motivo": "Temperatura alta (28°C)"}

⚙️ Configuração
Limiares de Automação
TEMP_LIGAR    = 30    # Liga ventilador acima de 30°C
TEMP_DESLIGAR = 25    # Desliga ventilador abaixo de 25°C
UMID_LIGAR    = 70    # Liga umidificador acima de 70%
UMID_DESLIGAR = 50    # Desliga umidificador abaixo de 50%

📁 Estrutura do Projeto
TEC502-P1/
├── README.md
├── Server/
│   ├── server.py          # Servidor principal (TCP + UDP)
│   ├── Dockerfile
│   └── docker-compose.yml
├── Client/
│   ├── client.py          # Painel do operador (interativo)
│   ├── atuador_vent.py    # Ventilador (simula atuador)
│   ├── atuador_umid.py    # Umidificador (simula atuador)
│   ├── Dockerfile
│   └── docker-compose.yml
└── Sensors/
    ├── sensor_temp.py     # Sensor de temperatura (simula leitura)
    ├── sensor_umid.py     # Sensor de umidade (simula leitura)
    ├── Dockerfile
    └── docker-compose.yml