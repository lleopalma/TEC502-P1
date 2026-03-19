import socket

host = "localhost"
port = 12345

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((host, port))
    s.sendall("atuador".encode())

    while True:
        comando = s.recv(1024).decode()
        print("Comando recebido:", comando)