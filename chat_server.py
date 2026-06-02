from __future__ import annotations

import socket
import threading
from datetime import datetime
from typing import Optional

HOST = "127.0.0.1"
PORT = 5000

# Memória compartilhada entre as threads do servidor.
clientes: dict[socket.socket, str] = {}
historico: list[str] = []

# Sincronização para proteger clientes e historico.
clientes_lock = threading.Lock()


def agora() -> str:
    return datetime.now().strftime("%H:%M:%S")


def enviar_linha(conn: socket.socket, texto: str) -> None:
    conn.sendall((texto + "\n").encode("utf-8"))


def broadcast(mensagem: str) -> None:
    with clientes_lock:
        conexoes = list(clientes.keys())

    for conn in conexoes:
        try:
            enviar_linha(conn, mensagem)
        except OSError:
            pass


def registrar_cliente(conn: socket.socket, nome: str) -> list[str]:
    with clientes_lock:
        clientes[conn] = nome
        historico_recente = historico[-5:]
        total = len(clientes)

    print(f"[SERVER] {nome} entrou. Clientes conectados: {total}")
    return historico_recente


def remover_cliente(conn: socket.socket) -> Optional[str]:
    with clientes_lock:
        nome = clientes.pop(conn, None)
        total = len(clientes)

    if nome:
        print(f"[SERVER] {nome} saiu. Clientes conectados: {total}")
    return nome


def salvar_no_historico(mensagem: str) -> None:
    with clientes_lock:
        historico.append(mensagem)
        if len(historico) > 50:
            historico.pop(0)


def tratar_cliente(conn: socket.socket, endereco: tuple[str, int]) -> None:
    nome: Optional[str] = None
    thread_nome = threading.current_thread().name

    try:
        arquivo = conn.makefile("r", encoding="utf-8")
        enviar_linha(conn, "Digite seu nome:")
        nome = arquivo.readline().strip() or f"Usuario-{endereco[1]}"

        historico_recente = registrar_cliente(conn, nome)
        enviar_linha(conn, "--- Historico recente ---")
        for item in historico_recente:
            enviar_linha(conn, item)
        enviar_linha(conn, "--- Fim do historico ---")

        broadcast(f"[{agora()}] sistema: {nome} entrou no chat.")

        for linha in arquivo:
            texto = linha.strip()
            if not texto:
                continue
            if texto.lower() == "/sair":
                break

            mensagem = f"[{agora()}] {nome}: {texto}"
            salvar_no_historico(mensagem)
            print(f"[SERVER:{thread_nome}] {mensagem}")
            broadcast(mensagem)

    except ConnectionError:
        pass
    finally:
        nome_removido = remover_cliente(conn)
        if nome_removido:
            broadcast(f"[{agora()}] sistema: {nome_removido} saiu do chat.")
        conn.close()


def run_server(host: str = HOST, port: int = PORT, stop_event: Optional[threading.Event] = None) -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as servidor:
        servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        servidor.bind((host, port))
        servidor.listen()
        servidor.settimeout(0.5)
        print(f"[SERVER] Chat ouvindo em {host}:{port}")

        while stop_event is None or not stop_event.is_set():
            try:
                conn, endereco = servidor.accept()
            except socket.timeout:
                continue

            thread = threading.Thread(
                target=tratar_cliente,
                args=(conn, endereco),
                name=f"cliente-{endereco[1]}",
                daemon=True,
            )
            thread.start()
            print(f"[SERVER] Thread criada: {thread.name}")

        print("[SERVER] Encerrando servidor do demo.")


if __name__ == "__main__":
    run_server()
