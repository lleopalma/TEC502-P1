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

op_lock = threading.Lock()
vent_lock = threading.Lock()
umid_lock = threading.Lock()

# Utilitários

def montar_mensagem(**campos):
    return (json.dumps(campos, ensure_ascii=False) + "\n").encode("utf-8")


def enviar_para_lista(lista, **campos):
    mensagem = montar_mensagem(**campos)
    falhos = []
    for s in lista:
        try:
            s.sendall(mensagem)
        except Exception:
            falhos.append(s)
    for s in falhos:
        lista.remove(s)


def notificar_operadores(**campos):
    """Envia uma mensagem estruturada para todos os operadores conectados."""
    with op_lock:
        enviar_para_lista(operadores, **campos)


# Lógica da temperatura

ultimo_cmd_temp = None

def processar_temperatura(valor, endereco):
    global ultimo_cmd_temp

    print(f"Sensor temperatura {endereco}: {valor}°C")

    # Atualiza operadores com leitura estruturada do sensor
    notificar_operadores(
        tipo="sensor_update",
        dispositivo="temperatura",
        valor=valor,
        unidade="°C"
    )

    if override_ventilador:
        return

    if valor >= TEMP_LIGAR and ultimo_cmd_temp != "LIGAR":
        ultimo_cmd_temp = "LIGAR"
        print("Comando: LIGAR_VENTILADOR")
        with vent_lock:
            enviar_para_lista(ventiladores, tipo="comando", acao="LIGAR_VENTILADOR")
        notificar_operadores(
            tipo="atuador_update",
            dispositivo="ventilador",
            estado="LIGADO",
            override=False,
            motivo=f"Temperatura alta ({valor}°C)"
        )

    elif valor <= TEMP_DESLIGAR and ultimo_cmd_temp != "DESLIGAR":
        ultimo_cmd_temp = "DESLIGAR"
        print("Comando: DESLIGAR_VENTILADOR")
        with vent_lock:
            enviar_para_lista(ventiladores, tipo="comando", acao="DESLIGAR_VENTILADOR")
        notificar_operadores(
            tipo="atuador_update",
            dispositivo="ventilador",
            estado="DESLIGADO",
            override=False,
            motivo=f"Temperatura normalizada ({valor}°C)"
        )


# Lógica da umidade

ultimo_cmd_umid = None

def processar_umidade(valor, endereco):
    global ultimo_cmd_umid

    print(f"Sensor umidade {endereco}: {valor}%")

    # Atualiza operadores com leitura estruturada do sensor
    notificar_operadores(
        tipo="sensor_update",
        dispositivo="umidade",
        valor=valor,
        unidade="%"
    )

    if override_umidificador:
        return

    if valor >= UMID_LIGAR and ultimo_cmd_umid != "LIGAR":
        ultimo_cmd_umid = "LIGAR"
        print("Comando: LIGAR_UMIDIFICADOR")
        with umid_lock:
            enviar_para_lista(umidificadores, tipo="comando", acao="LIGAR_UMIDIFICADOR")
        notificar_operadores(
            tipo="atuador_update",
            dispositivo="umidificador",
            estado="LIGADO",
            override=False,
            motivo=f"Umidade alta ({valor}%)"
        )

    elif valor <= UMID_DESLIGAR and ultimo_cmd_umid != "DESLIGAR":
        ultimo_cmd_umid = "DESLIGAR"
        print("Comando: DESLIGAR_UMIDIFICADOR")
        with umid_lock:
            enviar_para_lista(umidificadores, tipo="comando", acao="DESLIGAR_UMIDIFICADOR")
        notificar_operadores(
            tipo="atuador_update",
            dispositivo="umidificador",
            estado="DESLIGADO",
            override=False,
            motivo=f"Umidade normalizada ({valor}%)"
        )


# Tratamento de clientSes TCP

def handle_client(client_socket, address):
    client_socket  # evita thread travada por cliente inativo
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

        if dados.get("tipo") != "identificacao":
            print(f"Mensagem inválida de {address}: esperado tipo=identificacao")
            client_socket.close()
            return

    except Exception as e:
        print(f"Erro ao identificar cliente {address}: {e}")
        client_socket.close()
        return

    dispositivo = dados.get("dispositivo", "").lower()

    if dispositivo == "ventilador":
        with vent_lock:
            ventiladores.append(client_socket)
        print(f"Conexão: ventilador registrado {address}")
        client_socket.sendall(montar_mensagem(
            tipo="confirmacao", mensagem="Registrado como VENTILADOR"
        ))

    elif dispositivo == "umidificador":
        with umid_lock:
            umidificadores.append(client_socket)
        print(f"Conexão: umidificador registrado {address}")
        client_socket.sendall(montar_mensagem(
            tipo="confirmacao", mensagem="Registrado como UMIDIFICADOR"
        ))

    else:
        with op_lock:
            operadores.append(client_socket)
        print(f"Conexão: operador registrado {address}")
        client_socket.sendall(montar_mensagem(
            tipo="confirmacao", mensagem="Conectado como OPERADOR. Aguardando dados..."
        ))

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

                if dados.get("tipo") != "override":
                    print(f"Mensagem ignorada de {address}: tipo={dados.get('tipo')}")
                    continue

                acao     = dados.get("acao", "")
                operador = dados.get("operador", "desconhecido")
                print(f"Override de '{operador}' em {address}: {acao}")

                if acao == "LIGAR_VENTILADOR":
                    override_ventilador = False
                    with vent_lock:
                        enviar_para_lista(ventiladores, tipo="comando", acao=acao)
                    notificar_operadores(
                        tipo="atuador_update",
                        dispositivo="ventilador",
                        estado="LIGADO",
                        override=False,
                        motivo=f"Override manual por '{operador}' — automação retomada"
                    )

                elif acao == "DESLIGAR_VENTILADOR":
                    override_ventilador = True
                    with vent_lock:
                        enviar_para_lista(ventiladores, tipo="comando", acao=acao)
                    notificar_operadores(
                        tipo="atuador_update",
                        dispositivo="ventilador",
                        estado="DESLIGADO",
                        override=True,
                        motivo=f"Override manual por '{operador}' — automação suspensa"
                    )

                elif acao == "LIGAR_UMIDIFICADOR":
                    override_umidificador = False
                    with umid_lock:
                        enviar_para_lista(umidificadores, tipo="comando", acao=acao)
                    notificar_operadores(
                        tipo="atuador_update",
                        dispositivo="umidificador",
                        estado="LIGADO",
                        override=False,
                        motivo=f"Override manual por '{operador}' — automação retomada"
                    )

                elif acao == "DESLIGAR_UMIDIFICADOR":
                    override_umidificador = True
                    with umid_lock:
                        enviar_para_lista(umidificadores, tipo="comando", acao=acao)
                    notificar_operadores(
                        tipo="atuador_update",
                        dispositivo="umidificador",
                        estado="DESLIGADO",
                        override=True,
                        motivo=f"Override manual por '{operador}' — automação suspensa"
                    )

                else:
                    print(f"Ação desconhecida de {address}: {acao}")

        except Exception:
            break

    with op_lock:
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

                if dados.get("tipo") != "status":
                    print(f"Mensagem ignorada de {address}: tipo={dados.get('tipo')}")
                    continue

                estado = dados.get("estado", "?")
                print(f"Status {dispositivo.upper()} {address}: {estado}")

                # Repassa o status ao operador de forma estruturada
                notificar_operadores(
                    tipo="atuador_update",
                    dispositivo=dispositivo,
                    estado=estado,
                    override=(
                        override_ventilador   if dispositivo == "ventilador"
                        else override_umidificador
                    ),
                    motivo=f"Confirmação do dispositivo"
                )

        except Exception:
            break

    # Notifica operadores que o atuador desconectou
    notificar_operadores(
        tipo="atuador_update",
        dispositivo=dispositivo,
        estado="DESCONECTADO",
        override=False,
        motivo=f"Atuador desconectado inesperadamente"
    )

    lk = vent_lock if dispositivo == "ventilador" else umid_lock
    lista = ventiladores if dispositivo == "ventilador" else umidificadores
    with lk:
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
                if dados.get("tipo") != "sensor" or dados.get("dispositivo") != "temperatura":
                    print(f"Mensagem inválida do sensor de temperatura: {dados}")
                    continue
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
                if dados.get("tipo") != "sensor" or dados.get("dispositivo") != "umidade":
                    print(f"Mensagem inválida do sensor de umidade: {dados}")
                    continue
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