import socket
def main():
    host = 'localhost'
    port = 12345
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect((host, port))
        print("Conectado ao servidor")
        while True:
            message = input("Digite uma mensagem (ou 'exit' para sair): ")
            if message.lower() == 'exit':
                break
            client_socket.sendall(message.encode())
            data = client_socket.recv(1024)
            print(f"Recebido do servidor: {data.decode()}")
    print("Desconectado do servidor")
    
if __name__ == "__main__":    
    main()