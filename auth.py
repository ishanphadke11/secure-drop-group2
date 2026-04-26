import json
import hashlib
import os
from crypto import generate_key_pair

# function checks if a user is already registered
def is_registered():
    return os.path.isfile("data/users.json") and os.path.getsize("data/users.json") > 0

# if user is registered, this function returns the user's info in json format
def load_user():
    if not is_registered():
        return None
    with open("data/users.json", "r") as file:
        return json.load(file)

# this function is called to write user info from a dictionary to the users.json file
def save_user(user):
    with open("data/users.json", "w") as file:
        json.dump(user, file, indent=4)

# function to collect user's information
def collect_user_info():
    name = input("Enter Full Name: ").strip()
    email = input("Enter Email Address: ").strip()

    while True:
        password = input("Enter Password: ").strip()
        confirmed_password = input("Re-enter Password: ")

        if password == confirmed_password:
            print("Passwords Match.")
            break
        else:
            print("Passwords do not match. Please try again.")

    return {
        "name": name,
        "email": email,
        "password": password
    }

# function to register user
def register_user():
    users = load_user()
    if users is None:
        users = []
    elif isinstance(users, dict):
        users = [users]

    user_info = collect_user_info()

    for user in users:
        if user["email"] == user_info["email"]:
            print("A user with that email already exists.")
            return

    user_info["password_hash"] = hash_password(user_info.pop("password"))
    key, cert = generate_key_pair(user_info["email"], user_info["name"])
    user_info["key"] = key
    user_info["cert"] = cert
    user_info["encryption_salt"] = os.urandom(16).hex()

    users.append(user_info)
    save_user(users)
    print("User Registered.")

# function takes plaintext password and hashes it
def hash_password(password):
    salt = os.urandom(16).hex()
    hash = hashlib.pbkdf2_hmac('sha256', password.encode(), bytes.fromhex(salt), 600_000).hex()
    return f"{salt}${hash}"

# function takes plaintext password and compares it to the stored hashed password
def verify_password(password, stored_password):
    salt, hash = stored_password.split("$")
    new_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), bytes.fromhex(salt), 600_000).hex()
    if new_hash == hash:
        return True
    else:
        return False

# function to collect login infromation and authenticate user by verifying password
def login_user():
    email = input("Enter Email Address: ")
    password = input("Enter Password: ")

    users = load_user()

    if isinstance(users, dict):
        users = [users]

    for user_info in users:
        if user_info["email"] == email and password != "":
            if verify_password(password, user_info["password_hash"]):
                print(f"Welcome, {user_info['name']}.")
                return {
                    "name": user_info["name"],
                    "email": user_info["email"],
                    "password": password,
                    "encryption_salt": user_info["encryption_salt"]
                }

    print("Email and Password Combination Invalid.")
    return None
