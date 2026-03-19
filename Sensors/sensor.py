import socket
import time
import random

host = "localhost"
port = 12345

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((host, port))
    s.sendall("sensor".encode())

    while True:
        temperatura = random.randint(20, 35)
        mensagem = f"temperatura:{temperatura}"
        s.sendall(mensagem.encode())
        time.sleep(5)