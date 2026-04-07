import socket
import threading
import json

# Listas separadas por tipo de cliente TCP
operadores     = []
ventiladores   = []
umidificadores = []

# Portas
TCP_PORT      = 12345
UDP_TEMP_PORT = 12346
UDP_UMID_PORT = 12347
HOST          = "0.0.0.0"

# Limiares
TEMP_LIGAR    = 30
TEMP_DESLIGAR = 25
UMID_LIGAR    = 70
UMID_DESLIGAR = 50

# Flags de override
override_ventilador   = False
override_umidificador = False

lock = threading.Lock()


# Utilitários

def montar_mensagem(**campos):
    """Serializa um dicionário para JSON + newline."""
    return json.dumps(campos, ensure_ascii=False) + "\n"


def enviar_para_lista(lista, **campos):
    """Envia uma mensagem JSON para todos os sockets de uma lista."""
    mensagem = montar_mensagem(**campos)
    falhos = []
    for s in lista:
        try:
            s.sendall(mensagem.encode("utf-8"))
        except Exception:
            falhos.append(s)
    for s in falhos:
        lista.remove(s)


def notificar_operadores(mensagem):
    with lock:
        enviar_para_lista(operadores, tipo="log", origem="servidor", mensagem=mensagem)


# Lógica da temperatura

ultimo_cmd_temp = None

def processar_temperatura(valor, endereco):
    global ultimo_cmd_temp

    log = f"Sensor temperatura {endereco}: {valor}°C"
    print(log)
    notificar_operadores(log)

    if override_ventilador:
        return

    if valor >= TEMP_LIGAR and ultimo_cmd_temp != "LIGAR":
        ultimo_cmd_temp = "LIGAR"
        print(f"Comando: LIGAR_VENTILADOR")
        notificar_operadores(f"Temperatura alta ({valor}°C) → LIGAR_VENTILADOR")
        with lock:
            enviar_para_lista(ventiladores, tipo="comando", acao="LIGAR_VENTILADOR")

    elif valor <= TEMP_DESLIGAR and ultimo_cmd_temp != "DESLIGAR":
        ultimo_cmd_temp = "DESLIGAR"
        print(f"Comando: DESLIGAR_VENTILADOR")
        notificar_operadores(f"Temperatura normalizada ({valor}°C) → DESLIGAR_VENTILADOR")
        with lock:
            enviar_para_lista(ventiladores, tipo="comando", acao="DESLIGAR_VENTILADOR")


# Lógica da umidade

ultimo_cmd_umid = None

def processar_umidade(valor, endereco):
    global ultimo_cmd_umid

    log = f"Sensor umidade {endereco}: {valor}%"
    print(log)
    notificar_operadores(log)

    if override_umidificador:
        return

    if valor >= UMID_LIGAR and ultimo_cmd_umid != "LIGAR":
        ultimo_cmd_umid = "LIGAR"
        print(f"Comando: LIGAR_UMIDIFICADOR")
        notificar_operadores(f"Umidade alta ({valor}%) → LIGAR_UMIDIFICADOR")
        with lock:
            enviar_para_lista(umidificadores, tipo="comando", acao="LIGAR_UMIDIFICADOR")

    elif valor <= UMID_DESLIGAR and ultimo_cmd_umid != "DESLIGAR":
        ultimo_cmd_umid = "DESLIGAR"
        print(f"Comando: DESLIGAR_UMIDIFICADOR")
        notificar_operadores(f"Umidade normalizada ({valor}%) → DESLIGAR_UMIDIFICADOR")
        with lock:
            enviar_para_lista(umidificadores, tipo="comando", acao="DESLIGAR_UMIDIFICADOR")


# Tratamento de clientes TCP

def handle_client(client_socket, address):
    buffer = ""
    try:
        while "\n" not in buffer:
            chunk = client_socket.recv(1024).decode("utf-8")
            if not chunk:
                client_socket.close()
                return
            buffer += chunk

        linha, _ = buffer.split("\n", 1)
        dados = json.loads(linha.strip())
    except Exception as e:
        print(f"Erro ao identificar cliente {address}: {e}")
        client_socket.close()
        return

    dispositivo = dados.get("dispositivo", "").lower()

    with lock:
        if dispositivo == "ventilador":
            ventiladores.append(client_socket)
            print(f"Conexão: ventilador registrado {address}")
            client_socket.sendall(montar_mensagem(
                tipo="confirmacao", mensagem="Registrado como VENTILADOR"
            ).encode("utf-8"))

        elif dispositivo == "umidificador":
            umidificadores.append(client_socket)
            print(f"Conexão: umidificador registrado {address}")
            client_socket.sendall(montar_mensagem(
                tipo="confirmacao", mensagem="Registrado como UMIDIFICADOR"
            ).encode("utf-8"))

        else:
            operadores.append(client_socket)
            print(f"Conexão: operador registrado {address}")
            client_socket.sendall(montar_mensagem(
                tipo="confirmacao", mensagem="Conectado como OPERADOR. Aguardando dados..."
            ).encode("utf-8"))

    if dispositivo not in ("ventilador", "umidificador"):
        loop_operador(client_socket, address)
    else:
        loop_atuador(client_socket, address, dispositivo)


def loop_operador(client_socket, address):
    global override_ventilador, override_umidificador

    buffer = ""
    while True:
        try:
            chunk = client_socket.recv(2048)
            if not chunk:
                break

            buffer += chunk.decode("utf-8")

            while "\n" in buffer:
                linha, buffer = buffer.split("\n", 1)
                linha = linha.strip()
                if not linha:
                    continue

                dados = json.loads(linha)
                acao = dados.get("acao", "")
                print(f"Override {address}: {acao}")

                if acao == "LIGAR_VENTILADOR":
                    override_ventilador = False
                    with lock:
                        enviar_para_lista(ventiladores, tipo="comando", acao=acao)
                    notificar_operadores(f"Override: {acao} — automação retomada")

                elif acao == "DESLIGAR_VENTILADOR":
                    override_ventilador = True
                    with lock:
                        enviar_para_lista(ventiladores, tipo="comando", acao=acao)
                    notificar_operadores(f"Override: {acao} — automação suspensa")

                elif acao == "LIGAR_UMIDIFICADOR":
                    override_umidificador = False
                    with lock:
                        enviar_para_lista(umidificadores, tipo="comando", acao=acao)
                    notificar_operadores(f"Override: {acao} — automação retomada")

                elif acao == "DESLIGAR_UMIDIFICADOR":
                    override_umidificador = True
                    with lock:
                        enviar_para_lista(umidificadores, tipo="comando", acao=acao)
                    notificar_operadores(f"Override: {acao} — automação suspensa")

        except Exception:
            break

    with lock:
        if client_socket in operadores:
            operadores.remove(client_socket)
    client_socket.close()
    print(f"Desconexão: operador {address}")


def loop_atuador(client_socket, address, dispositivo):
    buffer = ""
    while True:
        try:
            chunk = client_socket.recv(1024)
            if not chunk:
                break

            buffer += chunk.decode("utf-8")

            while "\n" in buffer:
                linha, buffer = buffer.split("\n", 1)
                linha = linha.strip()
                if not linha:
                    continue

                dados = json.loads(linha)
                if dados.get("tipo") == "status":
                    log = f"Atuador {dispositivo.upper()} {address}: {dados.get('dispositivo')}:{dados.get('estado')}"
                    print(log)
                    notificar_operadores(log)

        except Exception:
            break

    with lock:
        lista = ventiladores if dispositivo == "ventilador" else umidificadores
        if client_socket in lista:
            lista.remove(client_socket)
    client_socket.close()
    print(f"Desconexão: atuador {dispositivo} {address}")


# Servidores de rede

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
            try:
                dados = json.loads(data.decode("utf-8"))
                valor = int(dados["valor"])
                processar_temperatura(valor, address)
            except Exception as e:
                print(f"Mensagem inválida do sensor de temperatura: {e}")


def udp_umid_server():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp:
        udp.bind((HOST, UDP_UMID_PORT))
        print(f"Servidor UDP umidade pronto na porta {UDP_UMID_PORT}")

        while True:
            data, address = udp.recvfrom(2048)
            try:
                dados = json.loads(data.decode("utf-8"))
                valor = int(dados["valor"])
                processar_umidade(valor, address)
            except Exception as e:
                print(f"Mensagem inválida do sensor de umidade: {e}")


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