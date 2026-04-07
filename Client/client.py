import socket
import threading
import json
import os
import time

HOST = os.environ.get("SERVER_HOST", "servidor")
PORT = 12345

running  = True
exibindo = False


def enviar(sock, **campos):
    mensagem = json.dumps(campos, ensure_ascii=False) + "\n"
    sock.sendall(mensagem.encode("utf-8"))


def receber_mensagens_background(sock):
    global running, exibindo
    while running:
        try:
            dados = sock.recv(2048)
            if not dados:
                print("\nConexão encerrada pelo servidor.")
                running = False
                break

            if exibindo:
                for linha in dados.decode("utf-8").splitlines():
                    linha = linha.strip()
                    if not linha:
                        continue
                    try:
                        msg = json.loads(linha)
                        # Exibe de forma legível
                        tipo = msg.get("tipo", "")
                        if tipo == "log":
                            print(f"[{msg.get('origem','?')}] {msg.get('mensagem','')}")
                        else:
                            print(linha)
                    except Exception:
                        print(linha)
                time.sleep(1)
                if exibindo:
                    apagar_tela()

        except Exception:
            if running:
                print("\nErro ao receber dados do servidor.")
            running = False
            break


def exibir_status():
    global exibindo
    apagar_tela()
    print("=== Status do Sistema — ao vivo ===")
    print("Pressione Enter para voltar ao menu...\n")

    exibindo = True
    input()
    exibindo = False

    apagar_tela()


def enviar_override(sock, username):
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

            acoes = {
                "1": "LIGAR_VENTILADOR",
                "2": "DESLIGAR_VENTILADOR",
                "3": "LIGAR_UMIDIFICADOR",
                "4": "DESLIGAR_UMIDIFICADOR",
            }

            if escolha in acoes:
                acao = acoes[escolha]
                enviar(sock, tipo="override", acao=acao, operador=username)
                print(f"Override enviado: {acao}")
            elif escolha == "5" or escolha.lower() == "voltar":
                print("\nVoltando ao menu...")
                break
            else:
                print("Opção inválida.")

        except (EOFError, KeyboardInterrupt):
            running = False
            break
        except Exception:
            print("\nErro ao enviar mensagem.")
            running = False
            break


def menu():
    print("\n=== Menu do Operador ===")
    print("1. Enviar override")
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
        enviar(sock, tipo="identificacao", dispositivo="operador")

        confirmacao = json.loads(sock.recv(1024).decode("utf-8"))
        print(f"\nServidor: {confirmacao.get('mensagem')}")

        t_recv = threading.Thread(
            target=receber_mensagens_background,
            args=(sock,),
            daemon=True
        )
        t_recv.start()

        while running:
            escolha = menu()
            if escolha == "1":
                enviar_override(sock, username)
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
        print(f"Erro: servidor não encontrado em {HOST}:{PORT}.")
        print("Verifique se o servidor está rodando e se SERVER_HOST está correto.")
    except Exception as e:
        print(f"Erro: {e}")
    finally:
        running = False
        sock.close()
        print("Desconectado.")


if __name__ == "__main__":
    main()