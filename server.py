"""
handles application level behavior now
"""

import socket
import selectors
from connections import ClientState, queue_msg, close_connection, read_from_clients, write_to_client
from protocol import Message, MessageType, ProtocolError, extract_msgs, encode_msg

host, port = "localhost", 9999

selector = selectors.DefaultSelector() 

clients = {} # client_socket -> client (ClientState obj)
history = []


def broadcast(msg: Message):
    data = encode_msg(msg)

    for client in list(clients.values()):
        queue_msg(selector, client, data)

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
            history_msg = Message(MessageType.SYSTEM, {"text": history_payload})
            queue_msg(selector, client, encode_msg(history_msg))

            out = Message(MessageType.SYSTEM, {"text" : f"{client_id} joined the chat"})
            broadcast(out)

def disconnect_client(client):
    clients.pop(client.sock, None)

    close_connection(selector, client)

    name = client.name or client.client_id

    print(f"{name} disconnected")
    out = Message(MessageType.SYSTEM, {"text":f"{name} left the chat"})
    broadcast(out)

def handle_msg(client, msg):
    if msg.type == MessageType.SET_NAME:
        client.name = msg.data["name"]
    
    elif msg.type == MessageType.CHAT:
        text = msg.data["text"]

        sender = client.name or client.client_id

        history.append(f"[{sender}] : {text}\n")
        outgoing = Message(MessageType.CHAT, {"sender": sender, "text":text})
        broadcast(outgoing)

    elif msg.type == MessageType.RENAME:
        new_name = msg.data["name"]
        old_name = client.name or client.client_id

        client.name = new_name

        out = Message(MessageType.SYSTEM, {"text" : f"{old_name} renamed to {new_name}"})
        broadcast(out)


def service_client(key, mask): # mini dispatcher
    client = key.data

    if mask & selectors.EVENT_READ:
        still_connected, data = read_from_clients(client)

        if not still_connected:
            disconnect_client(client)
            return

        if data is not None:
            client.recv_buffer.extend(data)

            try:
                msgs = extract_msgs(client.recv_buffer)
            except ProtocolError:
                disconnect_client(client)
                return

            for msg in msgs:
                handle_msg(client, msg)

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