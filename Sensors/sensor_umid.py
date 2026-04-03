import socket
import time
import random

# Sensor de Umidade
# Envia leituras de umidade relativa via UDP ao servidor

HOST = "servidor"
PORT = 12347          # porta UDP exclusiva para umidade

sensor_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

print(f"Sensor de umidade iniciado. Enviando para {HOST}:{PORT} a cada {0.5}s\n")

while True:
    try:
        # Simula leitura: valores entre 40% e 80% de umidade relativa
        umidade = random.randint(40, 80)
        mensagem = f"umidade:{umidade}"

        sensor_socket.sendto(mensagem.encode("utf-8"), (HOST, PORT))
        print(f"Enviado → {mensagem}%")

        time.sleep(1)
    except KeyboardInterrupt:
        print("\nSensor de umidade encerrado.")
        break
    except Exception as e:
        print(f"\nErro no sensor de umidade: {e}")
        break