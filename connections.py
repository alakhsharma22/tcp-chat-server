"""
handles all the client connection (per-client) and low level socket IO
"""

import socket
import selectors
from dataclasses import dataclass, field

@dataclass
class ClientState:
    sock: socket.socket
    address: tuple
    client_id: str

    send_buffer: bytearray = field(default_factory=bytearray)
    recv_buffer: bytearray = field(default_factory=bytearray)

def queue_msg(selector, client, data: bytes):
    was_empty = not client.send_buffer
    client.send_buffer.extend(data)

    if was_empty:
        selector.modify(client.sock, selectors.EVENT_READ | selectors.EVENT_WRITE, data=client)

def close_connection(selector, client):
    sock = client.sock
    try:
        selector.unregister(sock)
    except Exception:
        pass

    try:
        sock.close()
    except Exception:
        pass

def read_from_clients(client):
    "Return False if connection is broken, else True and the data (bytes) (can be None)"
    try:
        data = client.sock.recv(4096)
    except BlockingIOError:
        return True, None
    
    except (ConnectionRefusedError, OSError):
        return False, None
    
    if not data:
        return False, None

    return True, data

def write_to_client(selector, client):
    """Return False if connection is broken, else True"""
    if not client.send_buffer:
        return True

    try:
        sent = client.sock.send(client.send_buffer)
    except BlockingIOError:
        return True

    except (BrokenPipeError, ConnectionRefusedError, OSError):
        return False

    del client.send_buffer[:sent] # remove the sent bytes from buffer, so next time remaining are sent

    if not client.send_buffer: # stop listening until we have something to send, as all sent now
        selector.modify(client.sock, selectors.EVENT_READ, data=client)

    return True