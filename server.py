"""
handles application level behavior now
"""

import socket
import selectors
from connections import ClientState, queue_msg, close_connection, read_from_clients, write_to_client

host, port = "localhost", 9999

selector = selectors.DefaultSelector() 

clients = {} # client_socket -> client (ClientState obj)
history = []


def broadcast(msg):
    for client in list(clients.values()):
        queue_msg(selector, client, msg)

def accept_connections(server_socket):
    while True:
        try:
            client_socket, addr = server_socket.accept()

        except BlockingIOError:
            break

        client_socket.setblocking(False)
        client_id = f"User-{addr[1]}"

        client = ClientState(client_socket, addr, client_id)
        clients[client_socket] = client

        selector.register(client_socket, selectors.EVENT_READ, data=client)
        print(f"[{client_id}] connected")

        if history:
            history_payload = ("Chat History\n" + "\n".join(history) + "\n----")
            queue_msg(selector, client, history_payload)

            broadcast(f"{client_id} joined the chat")

def disconnect_client(client):
    clients.pop(client.sock, None)

    close_connection(selector, client)

    print(f"{client.client_id} disconnected")
    broadcast(f"{client.client_id} left the chat")


def service_client(key, mask): # mini dispatcher
    client = key.data

    if mask & selectors.EVENT_READ:
        still_connected, text = read_from_clients(client)

        if not still_connected:
            disconnect_client(client)
            return

        if text is not None:
            formatted_msg = f"[{client.client_id}] : {text}\n"
            history.append(formatted_msg)
            broadcast(formatted_msg)

    if mask & selectors.EVENT_WRITE:
        still_connected = write_to_client(selector, client)

        if not still_connected:
            disconnect_client(client)
            return

def run_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    server_socket.bind((host, port))
    server_socket.listen()

    server_socket.setblocking(False)

    # Accept can succeed without blocking in EVENT_READ
    selector.register(server_socket, selectors.EVENT_READ, data=None)
    print(f"Server started on {host}:{port}")

    try:
        while True:
            events = selector.select()
            for key, mask in events:
                if key.data is None:
                    accept_connections(key.fileobj)
                else:
                    service_client(key, mask)

    except KeyboardInterrupt:
        print(f"Stopping server")

    finally:
        for client in list(clients.values()):
            try:
                selector.unregister(client.sock)
            except Exception:
                pass

            client.sock.close()

        selector.unregister(server_socket)
        server_socket.close()

        selector.close()

if __name__ == "__main__":
    run_server()

## first_client.py file will still run for the server.py file.