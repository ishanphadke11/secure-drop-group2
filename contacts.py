import json
import base64
import os
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from network import discover_users

# function takes plaintext password and encryption salt for user to generate aes key. This key is
# used to encrypt/decrpt contacts.json using Fernet
def generate_aes_key(password, salt):
    derived_aes_key = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=bytes.fromhex(salt),
        iterations=600_000
    )
    base_64_key = base64.urlsafe_b64encode(derived_aes_key.derive(password.encode()))
    return Fernet(base_64_key)


def load_contacts(session):
    if not os.path.isfile("data/contacts.json"):
        return []
    fernet = generate_aes_key(session["password"], session["encryption_salt"])
    with open("data/contacts.json", "rb") as file:
        encrypted = file.read()
    return json.loads(fernet.decrypt(encrypted).decode())


def save_contacts(contacts, session):
    fernet = generate_aes_key(session["password"], session["encryption_salt"])
    encrypted = fernet.encrypt(json.dumps(contacts).encode())
    with open("data/contacts.json", "wb") as file:
        file.write(encrypted)


def add_contacts(session):
    name = input("Enter Contact Name: ")
    email = input("Enter Contact Email: ")

    contacts = load_contacts(session)
    contacts.append({"name": name, "email": email})
    save_contacts(contacts, session)
    print("Contact Added")

def list_contacts(session):
    contacts = load_contacts(session)
    online_users = [{"name": c["name"], "email": c["email"], "contacts": [session["email"]]} for c in contacts]
    valid = []

    for user in online_users:
        for contact in contacts:
            if contact["email"] == user["email"]:
                if session["email"] in user.get("contacts", []):
                    valid.append(user)
                    
    print("The following contacts are online:")
    for v in valid:
        print(f"* {v['name']} <{v['email']}>")
