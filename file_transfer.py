import os
import json
import base64
import time
import hashlib
import socket

from cryptography import x509
from cryptography.fernet import Fernet
from contacts import load_contacts
from network import list_online_contacts
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes

CHUNK_SIZE = 4096
FILE_PORT = 50002

def generate_file_key():
    return Fernet.generate_key()

def encrypt_chunk(cipher, chunk):
    return cipher.encrypt(chunk)

def decrypt_chunk(cipher, chunk):
    return cipher.decrypt(chunk)

def chunk_file(file_path):
    with open(file_path, "rb") as f:
        while True:
            chunk = f.read(CHUNK_SIZE)
            if not chunk:
                break
            yield chunk

def compute_hash(file_path):
    sha = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha.update(chunk)
    return sha.hexdigest()

# read file and encrypt it with gen key, split into chunks, and send each chunk to recipient id
def send_file(session, recipient_ip, file_path, recipient_cert_bytes):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    file_key = generate_file_key()
    cipher = Fernet(file_key)

    file_id = str(time.time())
    seq = 0

    file_hash = compute_hash(file_path)
    start_packet = {
        "file_id": file_id,
        "start": True,
        "key": encrypt_file_key(file_key, recipient_cert_bytes),
        "sender": session["email"],
        "filename": os.path.basename(file_path)
    }
    sock.sendto(json.dumps(start_packet).encode(), (recipient_ip, FILE_PORT))

    for chunk in chunk_file(file_path):
        seq += 1
        encrypted = cipher.encrypt(chunk)
        packet = {
            "file_id": file_id,
            "seq": seq,
            "data": base64.b64encode(encrypted).decode(),
            "hash": file_hash,
            "sender": session["email"]
        }
        sock.sendto(json.dumps(packet).encode(), (recipient_ip, FILE_PORT))
        time.sleep(0.01)

    end_packet = {
        "file_id": file_id,
        "end": True
    }
    sock.sendto(json.dumps(end_packet).encode(), (recipient_ip, FILE_PORT))
    
    print("[+] File sent successfully")

RECEIVED_FILES = {}

# receives incoming packets and detects when a full file finished sendinh
def start_file_receiver():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("", FILE_PORT))

    while True:
        data, addr = sock.recvfrom(65535)
        try:
            packet = json.loads(data.decode())
            print(" packet received")
            if packet.get("start"):
                file_id = packet["file_id"]
                RECEIVED_FILES[file_id] = {
                    "chunks": {},
                    "hash": None,
                    "sender": packet["sender"],
                    "key": packet["key"],
                    "filename": packet.get("filename", f"received_{file_id}")
                }
                continue

            if packet.get("end"):
                file_id = packet["file_id"]
                print(f"[+] Finished receiving file from {RECEIVED_FILES[file_id]['sender']}")
                output_path = f"data/{RECEIVED_FILES[file_id]['filename']}"
                assemble_file(file_id, output_path)
                continue
            
            file_id = packet["file_id"]
            seq = packet["seq"]
            chunk = base64.b64decode(packet["data"])

            if file_id not in RECEIVED_FILES:
                continue

            if seq in RECEIVED_FILES[file_id]["chunks"]:
                continue

            RECEIVED_FILES[file_id]["chunks"][seq] = chunk
            RECEIVED_FILES[file_id]["hash"] = packet["hash"]

        except:
            continue

# takes received chunks in order, decrypts using shared key, checks hash for integrity, and writes file
def assemble_file(file_id, output_path):
    data = RECEIVED_FILES[file_id]
    chunks = data["chunks"]
    ordered = [chunks[k] for k in sorted(chunks.keys())]

    key = decrypt_file_key(data["key"])
    cipher = Fernet(key)

    decrypted = b"".join(cipher.decrypt(chunk) for chunk in ordered)

    sha = hashlib.sha256(decrypted).hexdigest()
    if sha != data["hash"]:
        print("[-] File corrupted or tampered!")
        return
    
    with open(output_path, "wb") as file:
        file.write(decrypted)
    
    print("[+] File received successfully")

# converts a recipient email into an ip so you can type in the email to send a file
def send_file_interface(session, recipient_email, file_path):
    contacts = load_contacts(session)
    online = list_online_contacts(session, contacts)
    recipient = next((u for u in online if u["email"] == recipient_email), None)
    if not recipient:
        print("[-] User not online or not a mutual contact")
        return
    send_file(session, recipient["ip"], file_path, recipient["cert"])

def start_receiver():
    import threading
    t = threading.Thread(target=start_file_receiver, daemon=True)
    t.start()

def encrypt_file_key(file_key, recipient_cert_bytes):
    cert = x509.load_pem_x509_certificate(recipient_cert_bytes)
    public_key = cert.public_key()
    encrypted_key = public_key.encrypt(
        file_key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    return base64.b64encode(encrypted_key).decode()

def decrypt_file_key(encrypted_key_b64):
    from auth import load_user
    from cryptography.hazmat.primitives.serialization import load_pem_private_key
    user_info = load_user()
    if isinstance(user_info, list):
        user_info = user_info[0]
    with open(user_info["key"], "rb") as f:
        private_key = load_pem_private_key(f.read(), password=None)
    encrypted_key = base64.b64decode(encrypted_key_b64)
    return private_key.decrypt(
        encrypted_key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )

