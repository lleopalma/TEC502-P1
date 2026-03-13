import socket

host = 'localhost'
port = 12345

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sensor1_socket:
    sensor1_socket.bind((host, port))
    sensor1_socket.listen()

    print("Servidor aguardando conexão...")

    connection, addr = sensor1_socket.accept()
    with connection:
        print("Conectado a:", addr)

        while True:
            data = connection.recv(1024)
            if not data:
                break

            connection.sendall(data)