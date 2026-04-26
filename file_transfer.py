import os
import json
import base64
import time
import hashlib
import socket
from cryptography.fernet import Fernet
from network import ONLINE_USERS
from contacts import load_contacts

CHUNK_SIZE = 4096
FILE_PORT = 50001

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
def send_file(session, recipient_ip, file_path):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    file_key = generate_file_key()
    cipher = Fernet(file_key)

    file_id = str(time.time())
    seq = 0

    file_hash = compute_hash(file_path)
    start_packet = {
        "file_id": file_id,
        "start": True,
        "key": base64.b64encode(file_key).decode(),
        "sender": session["email"]
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
    sock.bind(("", FILE_PORT))

    while True:
        data, addr = sock.recvfrom(65535)
        try:
            packet = json.loads(data.decode())
            print(" packet recieved")
            if packet.get("start"):
                file_id = packet["file_id"]
                RECEIVED_FILES[file_id] = {
                    "chunks": {},
                    "hash": None,
                    "sender": packet["sender"],
                    "key": packet["key"]
                }
                continue

            if packet.get("end"):
                file_id = packet["file_id"]
                print(f"[+] Finished recieving file from {RECEIVED_FILES[file_id]['sender']}")
                output_path = f"recieved_{file_id}.bin"
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
    full_encrypted = b"".join(ordered)
    
    key = base64.b64decode(data["key"])
    cipher = Fernet(key)

    decrypted = cipher.decrypt(full_encrypted)

    sha = hashlib.sha256(decrypted).hexdigest()

    if sha != data["hash"]:
        print("[-] File corrupted or tampered!")
        return
    
    with open(output_path, "wb") as f:
        f.write(decrypted)
    
    print("[+] File received successfully")

# converts a recipient email into an ip so you can type in the email to send a file
def send_file_interface(session, recipient_email, file_path):
    recipient_ip = resolve_ip_by_email(recipient_email)
    if not recipient_ip:
        print("[-] User not online")
        return
    
    send_file(session, recipient_ip, file_path)

def start_receiver():
    import threading
    t = threading.Thread(target=start_file_receiver, daemon=True)
    t.start()

# looks up the online user list to find the correct ip address for an email
def resolve_ip_by_email(email):
    for user in ONLINE_USERS:
        if user["email"] == email:
            return user.get("ip")
    return None
