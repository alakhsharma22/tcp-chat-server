import socket
import selectors
from dataclasses import dataclass, field

host, port = "localhost", 9999

selector = selectors.DefaultSelector() 

clients = {} # client_socket -> client (ClientState obj)
history = []

"""
Create a dataclass instead of client_sockets set as we might need to store other state conditions
of a client such as user_name, input_buff, output_buff, etc.
"""
@dataclass
class ClientState:
    sock: socket.socket
    address: tuple
    client_id: str

    send_buffer: bytearray = field(default_factory=bytearray)

def queue_msg(client, msg):
    was_empty = not client.send_buffer
    client.send_buffer.extend(msg.encode('utf-8'))

    if was_empty:
        selector.modify(client.sock, selectors.EVENT_READ | selectors.EVENT_WRITE, data=client)

def broadcast(msg):
    for client in list(clients.values()):
        queue_msg(client, msg)

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
            queue_msg(client, history_payload)

            broadcast(f"{client_id} joined the chat")

def disconnect_client(client):
    sock = client.sock
    clients.pop(sock, None)

    try:
        selector.unregister(sock)
    except Exception:
        pass

    try:
        sock.close()
    except Exception:
        pass

    print(f"{client.client_id} disconnected")
    broadcast(f"{client.client_id} left the chat")

def read_from_clients(client):
    try:
        data = client.sock.recv(4096)
    except BlockingIOError:
        return True

    except (ConnectionRefusedError, OSError):
        disconnect_client(client)
        return False

    if not data:
        disconnect_client(client)
        return False

    try:
        text = data.decode('utf-8')
    except UnicodeDecodeError:
        disconnect_client(client)
        return False

    if not text:
        return True

    formatted_msg = f"[{client.client_id}] : {text}\n"
    history.append(formatted_msg)
    broadcast(formatted_msg)

    return True

def write_to_client(client):
    if not client.send_buffer:
        return

    try:
        sent = client.sock.send(client.send_buffer)
    except BlockingIOError:
        return

    except (BrokenPipeError, ConnectionRefusedError, OSError):
        disconnect_client(client)
        return

    del client.send_buffer[:sent] # remove the sent bytes from buffer, so next time remaining are sent

    if not client.send_buffer: # stop listening until we have something to send, as all sent now
        selector.modify(client.sock, selectors.EVENT_READ, data=client)

def service_client(key, mask): # mini dispatcher
    client = key.data

    if mask & selectors.EVENT_READ:
        still_connected = read_from_clients(client)

        if not still_connected:
            return

    if mask & selectors.EVENT_WRITE:
        write_to_client(client)

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