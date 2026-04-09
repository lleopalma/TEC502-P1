import socket
import json
import os
import time

# Atuador: Umidificador
# Conecta via TCP, recebe comandos e envia status no formato JSON

HOST = os.environ.get("SERVER_HOST", "servidor")
PORT = 12345
RETRY_INTERVAL = 5


def enviar(s, **campos):
    mensagem = json.dumps(campos, ensure_ascii=False) + "\n"
    s.sendall(mensagem.encode("utf-8"))


def ler_linha(s, buffer):
    """Lê do socket até ter uma linha completa, retorna (linha, buffer_restante)."""
    while "\n" not in buffer:
        chunk = s.recv(1024).decode("utf-8")
        if not chunk:
            raise ConnectionError("Conexão encerrada pelo servidor.")
        buffer += chunk
    linha, buffer = buffer.split("\n", 1)
    return linha.strip(), buffer


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
        enviar(s, tipo="identificacao", dispositivo="umidificador")

        # Confirmação do servidor — usa buffer para não perder bytes extras
        buffer = ""
        linha, buffer = ler_linha(s, buffer)
        confirmacao = json.loads(linha)
        assert confirmacao.get("tipo") == "confirmacao"
        print(f"Servidor: {confirmacao.get('mensagem')}")
        print("Aguardando comandos...\n")

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

                if dados.get("tipo") != "comando":
                    continue

                acao = dados.get("acao", "")

                if acao == "LIGAR_UMIDIFICADOR":
                    print(f"Comando recebido: {acao}")
                    print("Umidificador LIGADO (umidade baixa detectada)\n")
                    enviar(s, tipo="status", dispositivo="umidificador", estado="LIGADO")

                elif acao == "DESLIGAR_UMIDIFICADOR":
                    print(f"Comando recebido: {acao}")
                    print("Umidificador DESLIGADO (umidade normalizada)\n")
                    enviar(s, tipo="status", dispositivo="umidificador", estado="DESLIGADO")

                else:
                    print(f"Comando desconhecido: {acao}")

    except Exception as e:
        print(f"Erro na conexão: {e}")
    finally:
        s.close()

    print(f"Reconectando em {RETRY_INTERVAL}s...\n")
    time.sleep(RETRY_INTERVAL)