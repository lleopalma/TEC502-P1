import socket
import time
import random
import os

# Sensor de Temperatura
# Envia leituras de temperatura via UDP ao servidor
# SERVER_HOST pode ser definido via variável de ambiente:
#   - mesmo computador / mesmo compose: deixa vazio (usa "servidor" pelo DNS Docker)
#   - computador diferente: SERVER_HOST=<IP do servidor>

HOST = os.environ.get("SERVER_HOST", "servidor")
PORT = 12346

sensor_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

print(f"Sensor de temperatura iniciado. Enviando para {HOST}:{PORT} a cada 1s\n")

while True:
    try:
        temperatura = random.randint(20, 35)
        mensagem = f"temperatura:{temperatura}"

        sensor_socket.sendto(mensagem.encode("utf-8"), (HOST, PORT))
        print(f"Enviado: {mensagem}°C")

        time.sleep(1)
    except KeyboardInterrupt:
        print("\nSensor de temperatura encerrado.")
        break
    except Exception as e:
        print(f"\nErro no sensor de temperatura: {e}")
        break