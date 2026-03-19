import socket
import threading

clients = []

def handle_client(client_socket, address):
    print(f"Cliente conectado: {address}")

    while True:
        try:
            data = client_socket.recv(2048)

            if not data:
                break

            message = data.decode("utf-8")
            print(f"Mensagem de {address}: {message}")

            broadcast(message, client_socket)

        except:
            break

    print(f"Cliente desconectado: {address}")
    clients.remove(client_socket)
    client_socket.close()


def broadcast(message, sender_socket):
    for client in clients:
        if client != sender_socket:
            try:
                client.sendall(message.encode("utf-8"))
            except:
                client.close()
                clients.remove(client)


def main():
    host = 'localhost'
    port = 12345

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        try:
            server_socket.bind((host, port))
            server_socket.listen()
            print("\nServidor aguardando conexões...")

            while True:
                client_socket, address = server_socket.accept()
                clients.append(client_socket)

                thread = threading.Thread(
                    target=handle_client,
                    args=(client_socket, address)
                )
                thread.start()

        except Exception as e:
            print(f"\nErro ao inicializar o servidor: {e}")


if __name__ == "__main__":
    main()