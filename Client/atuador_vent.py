import socket
import os

# Atuador: Ventilador
# Conecta via TCP e aguarda comandos do servidor
# SERVER_HOST pode ser definido via variável de ambiente:
#   - mesmo computador / mesmo compose: deixa vazio (usa "servidor" pelo DNS Docker)
#   - computador diferente: SERVER_HOST=<IP do servidor>

HOST = os.environ.get("SERVER_HOST", "servidor")
PORT = 12345

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))

    s.sendall("ventilador".encode("utf-8"))

    confirmacao = s.recv(1024).decode("utf-8").strip()
    print(f"Servidor: {confirmacao}")
    print("Aguardando comandos...\n")

    buffer = ""
    while True:
        try:
            dados = s.recv(1024).decode("utf-8")
            if not dados:
                print("Conexão encerrada pelo servidor.")
                break

            buffer += dados
            while "\n" in buffer:
                linha, buffer = buffer.split("\n", 1)
                comando = linha.strip()
                if not comando:
                    continue

                if comando == "LIGAR_VENTILADOR":
                    print("COMANDO RECEBIDO: LIGAR_VENTILADOR")
                    print("Ventilador LIGADO (temperatura alta detectada)\n")
                    s.sendall("STATUS_VENTILADOR:LIGADO\n".encode("utf-8"))

                elif comando == "DESLIGAR_VENTILADOR":
                    print("COMANDO RECEBIDO: DESLIGAR_VENTILADOR")
                    print("Ventilador DESLIGADO (temperatura normalizada)\n")
                    s.sendall("STATUS_VENTILADOR:DESLIGADO\n".encode("utf-8"))

                else:
                    print(f"Comando desconhecido: {comando}")

        except Exception as e:
            print(f"Erro na conexão: {e}")
            break