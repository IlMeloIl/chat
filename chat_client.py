from __future__ import annotations

import socket
import sys
import threading

HOST = "127.0.0.1"
PORT = 5000


def receber_mensagens(sock: socket.socket) -> None:
    try:
        arquivo = sock.makefile("r", encoding="utf-8")
        for linha in arquivo:
            print(linha.rstrip())
    except OSError:
        pass
    finally:
        print("Conexão encerrada pelo servidor.")


def main() -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((HOST, PORT))

        thread_recebimento = threading.Thread(
            target=receber_mensagens,
            args=(sock,),
            name="recebedor",
            daemon=True,
        )
        thread_recebimento.start()

        try:
            while True:
                texto = input()
                sock.sendall((texto + "\n").encode("utf-8"))
                if texto.lower() == "/sair":
                    break
        except (KeyboardInterrupt, EOFError):
            sock.sendall(b"/sair\n")

    sys.exit(0)


if __name__ == "__main__":
    main()
