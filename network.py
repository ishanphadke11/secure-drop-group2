import socket
import json
import threading
import time

ONLINE_USERS = []
PORT = 50000


def start_listener():
    def listen():
        global ONLINE_USERS
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(('', PORT))

        while True:
            data, addr = s.recvfrom(4096)
            try:
                user = json.loads(data.decode())
                if user not in ONLINE_USERS:
                    ONLINE_USERS.append(user)
            except:
                continue

    thread = threading.Thread(target=listen, daemon=True)
    thread.start()


def broadcast_presence(session, contacts):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    contact_emails = [c["email"] for c in contacts]
    message = json.dumps({
        "name": session["name"],
        "email": session["email"],
        "contacts": contacts
    })

    s.sendto(message.encode(), ('<broadcast>', PORT))

def discover_users(session, contacts):
    global ONLINE_USERS
    ONLINE_USERS = []

    broadcast_presence(session, contacts)

    time.sleep(2)

    return ONLINE_USERS
