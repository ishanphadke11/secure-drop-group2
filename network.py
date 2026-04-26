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

def start_broadcaster(session, contacts):
    def loop():
        while True:
            broadcast_presence(session, contacts)
            time.sleep(2)
            
    thread = threading.Thread(target=loop, daemon=True)
    thread.start()

def broadcast_presence(session, contacts):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    # message
    message = json.dumps({
        "email": session["email"],
        "name": session["name"],
        "ip": socket.gethostbyname(socket.gethostname()),
        "contacts": [c["email"] for c in contacts]
    }).encode()
    # send message
    s.sendto(message, ('<broadcast>', PORT))

def discover_users(session, contacts):
    broadcast_presence(session, contacts)
    time.sleep(2)
    return ONLINE_USERS
