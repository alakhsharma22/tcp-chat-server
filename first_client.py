import socket
import sys
import threading
from protocol import MessageType, Message, encode_msg, ProtocolError, extract_msgs

host, port = "localhost", 9999

def display_message(message):
    if message.type == MessageType.CHAT:
        sender = message.data.get("sender", "Unknown")
        text = message.data.get("text", "")

        sys.stdout.write(f"\r\033[K[{sender}] : {text}\n> ")
        sys.stdout.flush()

    elif message.type == MessageType.SYSTEM:
        text = message.data.get("text", "")

        sys.stdout.write(f"\r\033[K[SYSTEM] {text}\n> ")
        sys.stdout.flush()

    elif message.type == MessageType.ERROR:
        text = message.data.get("text", "")

        sys.stdout.write(f"\r\033[K[ERROR] {text}\n> ")
        sys.stdout.flush()
        
def receive_message(sock):
    recv_buff = bytearray() # for current use, later can be added to an object

    while True:
        try:
            data = sock.recv(1024)
            if not data:
                break

            recv_buff.extend(data)
            msgs = extract_msgs(recv_buff)
            for msg in msgs:
                display_message(msg)

        except ProtocolError as ex:
            print(f"PE : {ex}")
            break

        except OSError:
            break


def start_client():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        sock.connect((host, port))
        print("Connected to the server.")
    except:
        print("server is offline")
        return

    name = input("Enter user name >")
    out = Message(MessageType.SET_NAME, {"name" : name})
    sock.sendall(encode_msg(out))

    recv_thread = threading.Thread(target=receive_message, args=(sock,), daemon=True)
    recv_thread.start()

    while True:
        try:
            user_input = input("> ")
            if user_input.lower() == "exit":
                break

            outgoing = Message(MessageType.CHAT, {"text": user_input})
            data = encode_msg(outgoing)
            sock.sendall(data)

        except:
            break

    sock.close()

if __name__ == "__main__":
    start_client()