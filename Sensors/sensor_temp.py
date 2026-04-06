import socket
import time
import random

# Sensor de Temperatura
# Envia leituras de temperatura via UDP ao servidor

HOST = "servidor"
PORT = 12346          # porta UDP exclusiva para temperatura

sensor_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

print(f"Sensor de temperatura iniciado. Enviando para {HOST}:{PORT} a cada {0.5}s\n")

while True:
    try:
        # Simula leitura: valores entre 20°C e 35°C
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