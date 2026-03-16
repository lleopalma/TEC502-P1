import socket, threading

clients = []

def main():
    host = 'localhost'
    port = 12345

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        try:
            server_socket.bind((host, port))
            server_socket.listen()
            print("\nServidor aguardando conexões...")

            continuar = True
            while continuar:
                client_socket, address = server_socket.accept()
                print(f"\nConexão estabelecida com {address}")
                clients.append(client_socket)
                

        except Exception as e:
            print(f"\nErro ao inicializar o servidor: {e}")

if __name__ == "__main__":
    main()