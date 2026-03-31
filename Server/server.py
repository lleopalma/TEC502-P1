import socket
import threading

# ──────────────────────────────────────────────
# Listas separadas por tipo de cliente TCP
# ──────────────────────────────────────────────
operadores    = []  # clientes humanos (client.py)
ventiladores  = []  # atuadores de temperatura
umidificadores = [] # atuadores de umidade

# Portas
TCP_PORT      = 12345
UDP_TEMP_PORT = 12346  # sensor de temperatura
UDP_UMID_PORT = 12347  # sensor de umidade
HOST          = "localhost"

# Limiares
TEMP_LIGAR    = 30  # °C → liga ventilador
TEMP_DESLIGAR = 25
UMID_LIGAR    = 70  # %  → liga umidificador
UMID_DESLIGAR = 50

# Flags de override — True = operador assumiu o controle, automação suspensa
override_ventilador   = False
override_umidificador = False

lock = threading.Lock()


# ──────────────────────────────────────────────
# Utilitários de envio
# ──────────────────────────────────────────────

def enviar_para_lista(lista, mensagem):
    """Envia uma mensagem para todos os sockets de uma lista."""
    mortos = []
    for s in lista:
        try:
            s.sendall(mensagem.encode("utf-8"))
        except Exception:
            mortos.append(s)
    for s in mortos:
        lista.remove(s)


def notificar_operadores(mensagem):
    with lock:
        enviar_para_lista(operadores, f"[SERVIDOR] {mensagem}\n")


# ──────────────────────────────────────────────
# Lógica de negócio: temperatura
# ──────────────────────────────────────────────

ultimo_cmd_temp = None

def processar_temperatura(valor, endereco):
    global ultimo_cmd_temp

    log = f"Sensor de temperatura {endereco}: {valor}°C"
    print(log)
    notificar_operadores(log)

    # Operador no controle — ignora limiares
    if override_ventilador:
        return

    if valor >= TEMP_LIGAR and ultimo_cmd_temp != "LIGAR":
        ultimo_cmd_temp = "LIGAR"
        cmd = "LIGAR_VENTILADOR"
        print(f"  → {cmd}")
        notificar_operadores(f"Temperatura alta! Enviando: {cmd}")
        with lock:
            enviar_para_lista(ventiladores, cmd + "\n")

    elif valor <= TEMP_DESLIGAR and ultimo_cmd_temp != "DESLIGAR":
        ultimo_cmd_temp = "DESLIGAR"
        cmd = "DESLIGAR_VENTILADOR"
        print(f"  → {cmd}")
        notificar_operadores(f"Temperatura normalizada. Enviando: {cmd}")
        with lock:
            enviar_para_lista(ventiladores, cmd + "\n")


# ──────────────────────────────────────────────
# Lógica de negócio: umidade
# ──────────────────────────────────────────────

ultimo_cmd_umid = None

def processar_umidade(valor, endereco):
    global ultimo_cmd_umid

    log = f"Sensor de umidade {endereco}: {valor}%"
    print(log)
    notificar_operadores(log)

    # Operador no controle — ignora limiares
    if override_umidificador:
        return

    if valor >= UMID_LIGAR and ultimo_cmd_umid != "LIGAR":
        ultimo_cmd_umid = "LIGAR"
        cmd = "LIGAR_UMIDIFICADOR"
        print(f"  → {cmd}")
        notificar_operadores(f"Umidade alta! Enviando: {cmd}")
        with lock:
            enviar_para_lista(umidificadores, cmd + "\n")

    elif valor <= UMID_DESLIGAR and ultimo_cmd_umid != "DESLIGAR":
        ultimo_cmd_umid = "DESLIGAR"
        cmd = "DESLIGAR_UMIDIFICADOR"
        print(f"  → {cmd}")
        notificar_operadores(f"Umidade normalizada. Enviando: {cmd}")
        with lock:
            enviar_para_lista(umidificadores, cmd + "\n")


# ──────────────────────────────────────────────
# Tratamento de clientes TCP
# ──────────────────────────────────────────────

def handle_client(client_socket, address):
    """
    Todo cliente TCP envia uma linha de identificação ao conectar:
      "operador"      → painel humano
      "ventilador"    → atuador de temperatura
      "umidificador"  → atuador de umidade
    """
    try:
        dados = client_socket.recv(1024).decode("utf-8").strip()
    except Exception:
        client_socket.close()
        return

    tipo = dados.lower()

    with lock:
        if tipo == "ventilador":
            ventiladores.append(client_socket)
            print(f"Ventilador registrado: {address}")
            client_socket.sendall("Registrado como VENTILADOR\n".encode())
        elif tipo == "umidificador":
            umidificadores.append(client_socket)
            print(f"Umidificador registrado: {address}")
            client_socket.sendall("Registrado como UMIDIFICADOR\n".encode())
        else:
            operadores.append(client_socket)
            print(f"Operador conectado: {address}")
            client_socket.sendall("Conectado como OPERADOR. Aguardando dados...\n".encode())

    if tipo not in ("ventilador", "umidificador"):
        loop_operador(client_socket, address)
    else:
        loop_atuador(client_socket, address, tipo)


def loop_operador(client_socket, address):
    """Recebe mensagens do operador, interpreta comandos de override."""
    global override_ventilador, override_umidificador

    while True:
        try:
            dados = client_socket.recv(2048)
            if not dados:
                break
            mensagem = dados.decode("utf-8").strip()
            print(f"[OPERADOR {address}] {mensagem}")

            # LIGAR devolve o atuador à automação
            if mensagem == "LIGAR_VENTILADOR":
                override_ventilador = False
                with lock:
                    enviar_para_lista(ventiladores, mensagem + "\n")
                notificar_operadores(f"Override: {mensagem} — automação retomada")

            # DESLIGAR suspende a automação e assume controle
            elif mensagem == "DESLIGAR_VENTILADOR":
                override_ventilador = True
                with lock:
                    enviar_para_lista(ventiladores, mensagem + "\n")
                notificar_operadores(f"Override: {mensagem} — automação suspensa")

            elif mensagem == "LIGAR_UMIDIFICADOR":
                override_umidificador = False
                with lock:
                    enviar_para_lista(umidificadores, mensagem + "\n")
                notificar_operadores(f"Override: {mensagem} — automação retomada")

            elif mensagem == "DESLIGAR_UMIDIFICADOR":
                override_umidificador = True
                with lock:
                    enviar_para_lista(umidificadores, mensagem + "\n")
                notificar_operadores(f"Override: {mensagem} — automação suspensa")

            else:
                # Mensagem livre → reencaminha para outros operadores
                with lock:
                    for s in operadores:
                        if s is not client_socket:
                            try:
                                s.sendall(f"[OPERADOR] {mensagem}\n".encode())
                            except Exception:
                                pass

        except Exception:
            break

    with lock:
        if client_socket in operadores:
            operadores.remove(client_socket)
    client_socket.close()
    print(f"Operador desconectado: {address}")


def loop_atuador(client_socket, address, tipo):
    """Mantém a conexão do atuador aberta; detecta desconexão."""
    while True:
        try:
            dados = client_socket.recv(1024)
            if not dados:
                break
        except Exception:
            break

    with lock:
        lista = ventiladores if tipo == "ventilador" else umidificadores
        if client_socket in lista:
            lista.remove(client_socket)
    client_socket.close()
    print(f"Atuador ({tipo}) desconectado: {address}")


# ──────────────────────────────────────────────
# Servidores de rede
# ──────────────────────────────────────────────

def tcp_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as srv:
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind((HOST, TCP_PORT))
        srv.listen()
        print(f"Servidor TCP pronto na porta {TCP_PORT}")

        while True:
            client_socket, address = srv.accept()
            t = threading.Thread(target=handle_client, args=(client_socket, address), daemon=True)
            t.start()


def udp_temp_server():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp:
        udp.bind((HOST, UDP_TEMP_PORT))
        print(f"Servidor UDP temperatura pronto na porta {UDP_TEMP_PORT}")

        while True:
            data, address = udp.recvfrom(2048)
            mensagem = data.decode("utf-8").strip()

            if mensagem.startswith("temperatura:"):
                try:
                    valor = int(mensagem.split(":")[1])
                    processar_temperatura(valor, address)
                except ValueError:
                    print(f"Valor inválido recebido do sensor de temperatura: {mensagem}")


def udp_umid_server():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp:
        udp.bind((HOST, UDP_UMID_PORT))
        print(f"Servidor UDP umidade pronto na porta {UDP_UMID_PORT}")

        while True:
            data, address = udp.recvfrom(2048)
            mensagem = data.decode("utf-8").strip()

            if mensagem.startswith("umidade:"):
                try:
                    valor = int(mensagem.split(":")[1])
                    processar_umidade(valor, address)
                except ValueError:
                    print(f"Valor inválido recebido do sensor de umidade: {mensagem}")


def main():
    threads = [
        threading.Thread(target=tcp_server,      daemon=True),
        threading.Thread(target=udp_temp_server, daemon=True),
        threading.Thread(target=udp_umid_server, daemon=True),
    ]
    for t in threads:
        t.start()

    print("=== Servidor IoT iniciado. Pressione Ctrl+C para encerrar. ===\n")

    try:
        for t in threads:
            t.join()
    except KeyboardInterrupt:
        print("\nServidor encerrado.")


if __name__ == "__main__":
    main()