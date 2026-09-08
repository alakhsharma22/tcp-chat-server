import socket
import sys
import threading

host, port = "localhost", 9999

def receive_message(sock):
    while True:
        data = sock.recv(1024)
        text = data.decode('utf-8')
        sys.stdout.write("\r\033[K" + text + "> ")
        sys.stdout.flush()

def start_client():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        sock.connect((host, port))
        print("Connected to the server.")
    except:
        print("server is offline")
        return

    recv_thread = threading.Thread(target=receive_message, args=(sock,), daemon=True)
    recv_thread.start()

    while True:
        try:
            user_input = input("> ")
            if user_input.lower() == "exit":
                break

            # sys.stdout.write("\033[1A\033[2K")
            # sys.stdout.flush()
            sock.sendall(user_input.encode('utf-8'))

        except:
            break

    sock.close()

if __name__ == "__main__":
    start_client()