import socketserver
import threading

active_clients = set() # set for client_sockets 
clients_lock = threading.Lock() # consistency

history = [] 
history_lock = threading.Lock() # consistency

def broadcast(message):
    with clients_lock:
        for client_socket in list(active_clients):
            try:
                client_socket.sendall(message.encode('utf-8'))
            except Exception:
                active_clients.discard(client_socket)

class ThreadedTCPHandler(socketserver.BaseRequestHandler):
    def handle(self):
        client_id = f"User-{self.client_address[1]}"
        print(f"[{client_id}] Connected")

        with clients_lock:
            active_clients.add(self.request)

        with history_lock:
            if history:
                history_payload = "Chat_history\n" + "\n".join(history) + "\n----"
                self.request.sendall(history_payload.encode('utf-8'))

        broadcast(f"***{client_id} joined the chat\n")

        try:
            while True:
                data = self.request.recv(1024)
                if not data:
                    break
            
                text = data.decode('utf-8')
                if not text:
                    continue

                format_message = f"[{client_id}] : {text}\n"

                with history_lock:
                    history.append(format_message)

                broadcast(format_message)

        except:
            pass

        finally:
            with clients_lock:
                active_clients.discard(self.request)
            print(f"[{client_id}] Disconnected")
            broadcast(f"*** {client_id} left the chat\n")

# ThreadingMixIn automatically creates threads as a new connection hits the server
class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    daemon_threads = True
    allow_reuse_address = True

if __name__ == "__main__":
    host, port = "localhost", 9999

    server = ThreadedTCPServer((host, port), ThreadedTCPHandler)
    with server:
        print(f"Server started on {host}:{port}")
        server.serve_forever()