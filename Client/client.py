import socket, threading

running = True

def main():

    global running

    host = 'localhost'
    port = 12345

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        client_socket.connect((host, port))
        print("\nConectado ao servidor")

        username = input("\nDigite seu nome de usuário: ")

        thread2 = threading.Thread(target=send_messages, args=(client_socket, username))
        thread2.start()
        thread2.join()

    except:
        print("\nErro ao conectar ao servidor")

    finally:
        running = False
        client_socket.close()

def send_messages(client_socket, username):
    global running

    while running:
        message = input("\nDigite uma mensagem (ou 'exit' para sair): ")

        if message.lower() == 'exit':
            running = False
            break

        try:
            client_socket.sendall(f"{username}: {message}".encode("utf-8"))
        except:
            print("\nErro ao enviar dados para o servidor")
            running = False
            break

if __name__ == "__main__":
    main()