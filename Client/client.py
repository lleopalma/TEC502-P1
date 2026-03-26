import socket
import threading

# ──────────────────────────────────────────────
# Cliente Operador
# Painel humano: recebe notificações do servidor
# e pode enviar mensagens de override manual
# ──────────────────────────────────────────────

HOST = "localhost"
PORT = 12345

running = True


def receber_mensagens(sock):
    """Thread que fica escutando mensagens vindas do servidor."""
    global running
    while running:
        try:
            dados = sock.recv(2048)
            if not dados:
                print("\nConexão encerrada pelo servidor.")
                running = False
                break
            print(dados.decode("utf-8"), end="")
        except Exception:
            if running:
                print("\nErro ao receber dados do servidor.")
            running = False
            break


def enviar_mensagens(sock, username):
    """Thread que lê input do operador e envia ao servidor."""
    global running
    while running:
        try:
            mensagem = input("")
            if mensagem.lower() == "exit":
                running = False
                break
            if mensagem.strip():
                sock.sendall(f"{username}: {mensagem}".encode("utf-8"))
        except (EOFError, KeyboardInterrupt):
            running = False
            break
        except Exception:
            print("\nErro ao enviar mensagem.")
            running = False
            break


def main():
    global running

    print("=== Painel do Operador ===")
    username = input("Digite seu nome: ").strip() or "Operador"

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        sock.connect((HOST, PORT))

        # Identifica-se como operador
        sock.sendall("operador".encode("utf-8"))

        # Recebe confirmação do servidor
        confirmacao = sock.recv(1024).decode("utf-8").strip()
        print(f"\nServidor: {confirmacao}")
        print("(Digite 'exit' para sair)\n")

        # Inicia as duas threads: recepção e envio
        t_recv = threading.Thread(target=receber_mensagens, args=(sock,), daemon=True)
        t_send = threading.Thread(target=enviar_mensagens, args=(sock, username))

        t_recv.start()
        t_send.start()

        t_send.join()

    except ConnectionRefusedError:
        print("Erro: servidor não encontrado. Certifique-se de que server.py está rodando.")
    except Exception as e:
        print(f"Erro: {e}")
    finally:
        running = False
        sock.close()
        print("Desconectado.")


if __name__ == "__main__":
    main()