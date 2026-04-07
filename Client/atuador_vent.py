import socket
import json
import os
import time

# Atuador: Ventilador
# Conecta via TCP, recebe comandos e envia status no formato JSON

HOST = os.environ.get("SERVER_HOST", "servidor")
PORT = 12345
RETRY_INTERVAL = 5  # segundos entre tentativas de reconexão


def enviar(s, **campos):
    mensagem = json.dumps(campos, ensure_ascii=False) + "\n"
    s.sendall(mensagem.encode("utf-8"))


def conectar():
    while True:
        try:
            print(f"Tentando conectar ao servidor {HOST}:{PORT}...")
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((HOST, PORT))
            print("Conectado ao servidor.\n")
            return s
        except Exception as e:
            print(f"Falha na conexão: {e}. Tentando novamente em {RETRY_INTERVAL}s...")
            time.sleep(RETRY_INTERVAL)


while True:
    s = conectar()

    try:
        # Identificação
        enviar(s, tipo="identificacao", dispositivo="ventilador")

        # Confirmação do servidor
        confirmacao = json.loads(s.recv(1024).decode("utf-8"))
        print(f"Servidor: {confirmacao.get('mensagem')}")
        print("Aguardando comandos...\n")

        buffer = ""
        while True:
            chunk = s.recv(1024).decode("utf-8")
            if not chunk:
                print("Conexão encerrada pelo servidor.")
                break

            buffer += chunk
            while "\n" in buffer:
                linha, buffer = buffer.split("\n", 1)
                linha = linha.strip()
                if not linha:
                    continue

                dados = json.loads(linha)
                acao = dados.get("acao", "")

                if acao == "LIGAR_VENTILADOR":
                    print(f"Comando recebido: {acao}")
                    print("Ventilador LIGADO (temperatura alta detectada)\n")
                    enviar(s, tipo="status", dispositivo="ventilador", estado="LIGADO")

                elif acao == "DESLIGAR_VENTILADOR":
                    print(f"Comando recebido: {acao}")
                    print("Ventilador DESLIGADO (temperatura normalizada)\n")
                    enviar(s, tipo="status", dispositivo="ventilador", estado="DESLIGADO")

                else:
                    print(f"Comando desconhecido: {acao}")

    except Exception as e:
        print(f"Erro na conexão: {e}")
    finally:
        s.close()

    print(f"Reconectando em {RETRY_INTERVAL}s...\n")
    time.sleep(RETRY_INTERVAL)