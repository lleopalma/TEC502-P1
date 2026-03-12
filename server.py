import socket

host = 'localhost'
port = 12345

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((host, port))
    s.listen()

    print("Server waiting for connection...")

    conn, addr = s.accept()
    with conn:
        print("Connected:", addr)

        while True:
            data = conn.recv(1024)
            if not data:
                break

            conn.sendall(data)