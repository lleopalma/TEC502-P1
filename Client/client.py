import socket
import threading
import os
import time
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
        time.sleep(0.5)
        os.system("cls" if os.name == "nt" else "clear")


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

def menu():
    print("=== Menu do Operador ===")
    print("1. Enviar mensagem de override")
    print("2. Visualizar status do sistema")
    print("3. Sair")
    escolha = input("Escolha uma opção: ").strip()
    return escolha

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
        escolha = menu()
        if escolha == "1":
            print("\nModo Override ativado. Digite suas mensagens abaixo.")
            enviar_mensagens(sock, username)
        elif escolha == "2":
            print("\nVisualizando status do sistema...")
            receber_mensagens(sock)
        elif escolha == "3":
            print("\nSaindo...")
            running = False
        print("(Digite 'exit' para sair)\n")

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