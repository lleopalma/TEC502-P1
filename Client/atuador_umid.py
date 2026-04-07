import socket
import json
import os

# Atuador: Umidificador
# Conecta via TCP, recebe comandos e envia status no formato JSON

HOST = os.environ.get("SERVER_HOST", "servidor")
PORT = 12345

def enviar(s, **campos):
    mensagem = json.dumps(campos, ensure_ascii=False) + "\n"
    s.sendall(mensagem.encode("utf-8"))

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))

    # Identificação
    enviar(s, tipo="identificacao", dispositivo="umidificador")

    # Confirmação do servidor
    confirmacao = json.loads(s.recv(1024).decode("utf-8"))
    print(f"Servidor: {confirmacao.get('mensagem')}")
    print("Aguardando comandos...\n")

    buffer = ""
    while True:
        try:
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

                if acao == "LIGAR_UMIDIFICADOR":
                    print(f"Comando recebido: {acao}")
                    print("Umidificador LIGADO (umidade alta detectada)\n")
                    enviar(s, tipo="status", dispositivo="umidificador", estado="LIGADO")

                elif acao == "DESLIGAR_UMIDIFICADOR":
                    print(f"Comando recebido: {acao}")
                    print("Umidificador DESLIGADO (umidade normalizada)\n")
                    enviar(s, tipo="status", dispositivo="umidificador", estado="DESLIGADO")

                else:
                    print(f"Comando desconhecido: {acao}")

        except Exception as e:
            print(f"Erro na conexão: {e}")
            break