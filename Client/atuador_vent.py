import socket

# ──────────────────────────────────────────────
# Atuador: Ventilador
# Conecta via TCP e aguarda comandos do servidor
# baseados nas leituras do sensor de temperatura
# ──────────────────────────────────────────────

HOST = "localhost"
PORT = 12345

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))

    # Identifica-se ao servidor como ventilador
    s.sendall("ventilador".encode("utf-8"))

    # Confirmação do servidor
    confirmacao = s.recv(1024).decode("utf-8").strip()
    print(f"Servidor: {confirmacao}")
    print("Aguardando comandos...\n")

    # Loop de escuta de comandos
    buffer = ""
    while True:
        try:
            dados = s.recv(1024).decode("utf-8")
            if not dados:
                print("Conexão encerrada pelo servidor.")
                break

            buffer += dados
            # Processa linha por linha (comandos terminam em \n)
            while "\n" in buffer:
                linha, buffer = buffer.split("\n", 1)
                comando = linha.strip()
                if not comando:
                    continue

                if comando == "LIGAR_VENTILADOR":
                    print("COMANDO RECEBIDO: LIGAR_VENTILADOR")
                    print("   → Ventilador LIGADO (temperatura alta detectada)\n")

                elif comando == "DESLIGAR_VENTILADOR":
                    print("COMANDO RECEBIDO: DESLIGAR_VENTILADOR")
                    print("   → Ventilador DESLIGADO (temperatura normalizada)\n")

                else:
                    print(f"Comando desconhecido: {comando}")

        except Exception as e:
            print(f"Erro na conexão: {e}")
            break