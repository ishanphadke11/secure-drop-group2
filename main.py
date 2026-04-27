from auth import register_user, is_registered, login_user
from contacts import load_contacts, add_contacts, list_contacts
from file_transfer import send_file_interface, start_receiver
from network import start_listener, start_broadcaster, start_tcp_listener


def main():
    session = None
    if not is_registered():
        print("No users are registered with this client.")
        choice = input("Do you want to register a new user? (y/n)")
        if choice == 'y':
            session = register_user()
        else:
            print("Exiting SecureDrop")
            return

    while session is None:
        session = login_user()

    start_listener()
    start_receiver()
    start_broadcaster()
    start_tcp_listener(session)

    commands(session)

def commands(session):
    print("Type help for commands.")
    while True:
        raw = input("secure_drop> ").strip()
        command = raw.lower()
        if command == "help":
            print('"add" -> Add a new contact')
            print('"list" -> List all online contacts')
            print('"send" -> Transfer file to contact')
            print('"exit" -> Exit SecureDrop')

        elif command == "add":
            add_contacts(session)

        elif command == "list":
            list_contacts(session)

        elif command.startswith("send"):
            parts = raw.split()
            if len(parts) == 3:
                recipient = parts[1]
                file_path = parts[2]
            else:
                recipient = input("Enter recipient email: ")
                file_path = input("Enter file path: ")

            send_file_interface(session, recipient, file_path)

        elif command == "exit":
             print("Exiting SecureDrop.")
             break
        else:
            print("Unknown command.")

if __name__ == "__main__":
    main()
