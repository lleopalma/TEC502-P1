import socket
import time
import random

HOST = "localhost"
PORT = 12346

sensor_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

while True:
    temperatura = random.randint(20, 35)
    mensagem = f"temperatura:{temperatura}"

    sensor_socket.sendto(mensagem.encode(), (HOST, PORT))

    print("Enviado:", mensagem)

    time.sleep(3)