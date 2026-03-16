import socket, threading

def main():

    host = 'localhost'
    port = 12345

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        try:
            client_socket.connect((host, port))
            print("\nConectado ao servidor")
            username = input("\nDigite seu nome de usuário: ")

            thread1 = threading.Thread(target=receive_messages, args=[client_socket])
            thread2 = threading.Thread(target=send_messages, args=[client_socket, username])

            thread1.start()
            thread2.start()

        except:
            print("\nErro ao conectar ao servidor")
        
def receive_messages(client_socket):
    continuar = True
    while continuar:
        try:
            data = client_socket.recv(2048)
            if not data:
                continuar = False
            print(f"\nRecebido do servidor: {data.decode("utf-8")}")
        except:
            print("\nErro ao receber dados do servidor")
            continuar = False

def send_messages(client_socket, username):
    continuar = True
    while continuar:
        message = input("\nDigite uma mensagem (ou 'exit' para sair): ")
        if message.lower() == 'exit':
            continuar = False
        try:
            client_socket.sendall(f"{username}: {message}".encode("utf-8"))
        except:
            print("\nErro ao enviar dados para o servidor")
            continuar = False

if __name__ == "__main__":    
    main()