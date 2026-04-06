import socket
import time
import random
import os

# Sensor de Umidade
# Envia leituras de umidade relativa via UDP ao servidor
# SERVER_HOST pode ser definido via variável de ambiente:
#   - mesmo computador / mesmo compose: deixa vazio (usa "servidor" pelo DNS Docker)
#   - computador diferente: SERVER_HOST=<IP do servidor>

HOST = os.environ.get("SERVER_HOST", "servidor")
PORT = 12347

sensor_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

print(f"Sensor de umidade iniciado. Enviando para {HOST}:{PORT} a cada 1s\n")

while True:
    try:
        umidade = random.randint(40, 80)
        mensagem = f"umidade:{umidade}"

        sensor_socket.sendto(mensagem.encode("utf-8"), (HOST, PORT))
        print(f"Enviado: {mensagem}%")

        time.sleep(1)
    except KeyboardInterrupt:
        print("\nSensor de umidade encerrado.")
        break
    except Exception as e:
        print(f"\nErro no sensor de umidade: {e}")
        break