import socket
import threading
import json
import time
import copy


class Router:

    def __init__(self, config: dict, dcs: list):
        self.rcid = config["rcid"]
        self.asn = config["asn"]
        self.ip = config["ip"]
        self.port = config["port"]
        self.dcs = dcs
        self.neighbors = []

    def set_neighbors(self, neighbors: list):
        self.neighbors = neighbors

    def set_dcs(self, dcs):
        self.dcs = dcs

    def send_hello(self):  # Function to send hello messages to neighbors
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                while True:
                    for neighbor in self.neighbors:
                        message = f"Hello from Router {self.rcid}"
                        sock.sendto(message.encode(),
                                    (neighbor.ip, neighbor.port))
                        print(f"Sent hello message to Router {neighbor.rcid}")
                    time.sleep(10)  # Send hello messages every 5 seconds
        except Exception as e:
            raise e

    def receive_hello(self):  # Function to receive hello messages from neighbors
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                sock.bind((self.ip, self.port))
                while True:
                    data, addr = sock.recvfrom(1024)
                    print(f"Received hello message from {
                          addr}: {data.decode()}")
        except Exception as e:
            raise e

    def start(self):  # Start router
        # Start threads for sending and receiving hello messages
        send_thread = threading.Thread(target=self.send_hello)
        receive_thread = threading.Thread(target=self.receive_hello)

        send_thread.start()
        receive_thread.start()

        # Join threads to ensure the main program does not exit
        send_thread.join()
        receive_thread.join()

    def __str__(self) -> str:
        router = copy.copy(self)
        
        dict_neighbors = []
        for n in self.neighbors:
            dict_neighbors.append(n.__dict__)

        dict_dcs = []
        for dc in self.dcs:
            dict_dcs.append(dc.__dict__)

        router.neighbors = dict_neighbors
        router.dcs = dict_dcs
        return json.dumps(router.__dict__, indent=2)


class Neighbor():

    def __init__(self, config: dict):
        self.rcid = config["rcid"]
        self.asn = config["asn"]
        self.ip = config["ip"]
        self.port = config["port"]
        self.capacity = config["capacity"]
        self.cost = config["cost"]

    def __str__(self) -> str:
        return json.dumps(self.__dict__, indent=2)


class DataCenter():

    def __init__(self, config):
        self.dcid = config["dcid"]
        self.capacity = config["capacity"]
        self.cost = config["cost"]
