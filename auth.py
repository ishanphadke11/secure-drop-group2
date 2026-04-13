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
def save_user(user_info):
    with open("data/users.json", "w") as file:
        json.dump(user_info, file)

# function to collect user's information
def collect_user_info():
    name = input("Enter Full Name: ")
    email = input("Enter Email Address: ")

    while True:
        password = input("Enter Password: ")
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
    user_info = collect_user_info()
    user_info["password_hash"] = hash_password(user_info.pop("password"))
    key, cert = generate_key_pair(user_info["email"], user_info["name"])
    user_info["key"] = key
    user_info["cert"] = cert
    save_user(user_info)

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
    user_info = load_user()
    if user_info["email"] == email and verify_password(password, user_info["password_hash"]):
        print(f"Welcome, {user_info['name']}.")
        return True

    else:
        print("Email and Password combination invalid.")
        return False