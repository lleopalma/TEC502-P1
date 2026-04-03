import socket
import threading
import os
import time

HOST = "servidor"
PORT = 12345

running = True       # controla o programa inteiro
exibindo = False     # True quando o usuário está na tela de status

def receber_mensagens_background(sock):
    """
    Thread em background: recebe dados do servidor continuamente.
    Só imprime na tela quando a flag 'exibindo' estiver ativa.
    """
    global running, exibindo
    while running:
        try:
            dados = sock.recv(2048)
            if not dados:
                print("\nConexão encerrada pelo servidor.")
                running = False
                break
            if exibindo:
                print(dados.decode("utf-8").strip())
                time.sleep(1)
                if exibindo:
                    apagar_tela() 
        except Exception:
            if running:
                print("\nErro ao receber dados do servidor.")
            running = False
            break

def exibir_status():
    """
    Ativa o streaming ao vivo. As mensagens são impressas pela thread
    de background enquanto o usuário não pressionar Enter.
    """
    global exibindo
    apagar_tela()
    print("=== Status do Sistema — ao vivo ===")
    print("Pressione Enter para voltar ao menu...\n")

    exibindo = True
    input()          # bloqueia até o usuário pressionar Enter
    exibindo = False

    apagar_tela()

def enviar_mensagens(sock, username):
    """Envia mensagens de override. Digite 'voltar' para retornar ao menu."""
    global running
    print("\nModo Override ativado. Digite 'voltar' para retornar ao menu.\n")

    while running:
        try:
            print("1. LIGAR_VENTILADOR")
            print("2. DESLIGAR_VENTILADOR")
            print("3. LIGAR_UMIDIFICADOR")
            print("4. DESLIGAR_UMIDIFICADOR")
            print("5. Voltar ao menu")
            escolha = input("Escolha um comando: ").strip()
            if escolha == "1":
                comando = "LIGAR_VENTILADOR"
            elif escolha == "2":
                comando = "DESLIGAR_VENTILADOR"
            elif escolha == "3":
                comando = "LIGAR_UMIDIFICADOR"
            elif escolha == "4":
                comando = "DESLIGAR_UMIDIFICADOR"
            elif escolha == "5" or escolha.lower() == "voltar":
                print("\nVoltando ao menu...")
                break
            else:
                print("Comando inválido. Tente novamente.")
                continue

            print(f"OVERRIDE: {comando} (enviado por {username})")
            sock.sendall(comando.encode("utf-8"))
        except (EOFError, KeyboardInterrupt):
            running = False
            break
        except Exception:
            print("\nErro ao enviar mensagem.")
            running = False
            break

def menu():
    print("\n=== Menu do Operador ===")
    print("1. Enviar mensagem de override")
    print("2. Visualizar status do sistema")
    print("3. Sair")
    return input("Escolha uma opção: ").strip()

def apagar_tela():
    os.system("cls" if os.name == "nt" else "clear")

def main():
    global running

    print("=== Painel do Operador ===")
    username = input("Digite seu nome: ").strip() or "Operador"

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        sock.connect((HOST, PORT))
        sock.sendall("operador".encode("utf-8"))

        confirmacao = sock.recv(1024).decode("utf-8").strip()
        print(f"\nServidor: {confirmacao}")

        # Thread de recepção sempre ativa em background
        t_recv = threading.Thread(
            target=receber_mensagens_background,
            args=(sock,),
            daemon=True
        )
        t_recv.start()

        while running:
            escolha = menu()
            if escolha == "1":
                enviar_mensagens(sock, username)
                apagar_tela()
            elif escolha == "2":
                exibir_status()
            elif escolha == "3":
                print("\nSaindo...")
                running = False
            else:
                print("Opção inválida.")
                apagar_tela()

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