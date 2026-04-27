import socket
import json
import threading
import time
from cryptography import x509
from cryptography.x509.oid import NameOID
from auth import load_user

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
                ONLINE_USERS[:] = [u for u in ONLINE_USERS if u["ip"] != user["ip"]]
                ONLINE_USERS.append(user)
            except:
              continue

    thread = threading.Thread(target=listen, daemon=True)
    thread.start()

def start_broadcaster():
    def loop():
        while True:
            broadcast_presence()
            time.sleep(2)
            
    thread = threading.Thread(target=loop, daemon=True)
    thread.start()

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    finally:
        s.close()

def broadcast_presence():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    message = json.dumps({
        "ip": get_local_ip(),
        "port": 50001,
    }).encode()
    s.sendto(message, ('<broadcast>', PORT))
    s.close()

def perform_handshake(ip, port, session, contacts):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5)
        s.connect((ip, port))

        # send our certificate
        user_info = load_user()
        if isinstance(user_info, list):
            user_info = user_info[0]
        with open(user_info["cert"], "rb") as file:
            our_cert = file.read()
        s.sendall(our_cert)

        # recieve their certificate
        their_cert = s.recv(4096)
        s.close()

        their_cert_bytes = their_cert
        their_cert = x509.load_pem_x509_certificate(their_cert_bytes)
        their_email = their_cert.subject.get_attributes_for_oid(NameOID.EMAIL_ADDRESS)[0].value

        if any(c["email"] == their_email for c in contacts):
            their_name = their_cert.subject.get_attributes_for_oid(NameOID.COMMON_NAME)[0].value
            return {"name": their_name, "email": their_email, "ip": ip, "cert": their_cert_bytes}

    except:
        return None
    return None

def start_tcp_listener(session):
    def listen():
        from contacts import load_contacts
        user_info = load_user()
        if isinstance(user_info, list):
            user_info = user_info[0]
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(('', 50001))
        server.listen(5)

        while True:
            conn, addr = server.accept()
            try:
                their_cert_data = conn.recv(4096)
                their_cert = x509.load_pem_x509_certificate(their_cert_data)
                their_email = their_cert.subject.get_attributes_for_oid(NameOID.EMAIL_ADDRESS)[0].value

                contacts = load_contacts(session)
                if any(c["email"] == their_email for c in contacts):
                    with open(user_info["cert"], "rb") as file:
                        our_cert = file.read()
                    conn.sendall(our_cert)
                conn.close()
            except:
                conn.close()
    thread = threading.Thread(target=listen, daemon=True)
    thread.start()

def list_online_contacts(session, contacts):
    results = []
    for user in ONLINE_USERS:
        result = perform_handshake(user["ip"], user["port"], session, contacts)
        if result:
            results.append(result)
    return results