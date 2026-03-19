import socket
import threading

clients = []

TCP_PORT = 12345
UDP_PORT = 12346
HOST = "localhost"


def handle_client(client_socket, address):
    print("Cliente conectado:", address)

    while True:
        try:
            data = client_socket.recv(2048)
            if not data:
                break

            message = data.decode("utf-8")
            print("TCP:", message)

            broadcast(message)

        except:
            break

    clients.remove(client_socket)
    client_socket.close()


def broadcast(message):
    for client in clients:
        try:
            client.sendall(message.encode("utf-8"))
        except:
            pass


def tcp_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.bind((HOST, TCP_PORT))
        server_socket.listen()

        print("Servidor TCP pronto")

        while True:
            client_socket, address = server_socket.accept()
            clients.append(client_socket)

            thread = threading.Thread(
                target=handle_client,
                args=(client_socket, address)
            )
            thread.start()


def udp_server():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:
        udp_socket.bind((HOST, UDP_PORT))

        print("Servidor UDP pronto para sensores")

        while True:
            data, address = udp_socket.recvfrom(2048)

            message = data.decode("utf-8")
            print("Sensor:", message)

            broadcast(f"[SENSOR {address}] {message}")


def main():
    thread_tcp = threading.Thread(target=tcp_server)
    thread_udp = threading.Thread(target=udp_server)

    thread_tcp.start()
    thread_udp.start()


if __name__ == "__main__":
    main()