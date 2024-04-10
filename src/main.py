from setup import create_router

# Define router information (IP address)
IP = "localhost"
CONFIG_FILE = "config\\config.json"


def main():
    router_num = int(input("Which router would you like to run? "))
    router = create_router(CONFIG_FILE, router_num)
    if router:
        print("Type 'help' to get started.")
        router.start()


if __name__ == "__main__":
    main()
