import socket
import threading
import time

from setup import create_router

# Define router information (IP address)
IP = "localhost"
CONFIGS = ["..\\config\\R1.json", "..\\config\\R2.json", "..\\config\\R3.json", "..\\config\\R4.json"]


def main():
    config = int(input("Which router would you like to run? ")) - 1
    router = create_router(CONFIGS[config])
    router.start()


if __name__ == "__main__":
    main()
