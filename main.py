from auth import register_user, is_registered, login_user

def main():
    if not is_registered():
        print("No users are registered with this client.")
        choice = input("Do you want to register a new user? (y/n)")
        if choice == 'y':
            register_user()
            print("User Registered")

        print("Exiting SecureDrop")
        return

    if is_registered():
        print("User Is Registered. Login: ")
        login_user()




if __name__ == "__main__":
    main()
