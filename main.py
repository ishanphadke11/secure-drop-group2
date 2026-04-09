from auth import register_user, is_registered

def main():
    if not is_registered():
        print("No users are registered with this client.")
        choice = input("Do you want to register a new user? (y/n)")
        if choice == 'y':
            register_user()
            print("User Registered")

        print("Exiting SecureDrop")

if __name__ == "__main__":
    main()
