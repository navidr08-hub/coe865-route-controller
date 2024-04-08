import socket
import threading
import json
import time
import copy
import traceback as tb


COST_WEIGHT = 1
CAPACITY_WEIGHT = 1


class Router:

    def __init__(self, config: dict, dcs: list, neighbors: list):
        self.rcid = config["rcid"]
        self.asn = config["asn"]
        self.ip = config["ip"]
        self.port = config["port"]
        self.dcs = dcs
        self.neighbors = neighbors
        self.show_rcu = False
        self.shutdown_event = threading.Event()  # Event to signal shutdown
        self.input_thread = threading.Thread(target=self.get_input)

        # Initialize routing table with default route to each neighbor
        self.routing_table = [
            {
                "asn": neighbor.asn,
                "next_hop": neighbor.rcid,
                "interface": neighbor.port,
                "cost": self.composite_cost(neighbor.capacity, neighbor.cost)
            }
            for neighbor in neighbors]

    def set_show_rcu(self, value: bool):
        self.show_rcu = value

    @staticmethod
    def composite_cost(capacity, cost):
        return capacity*CAPACITY_WEIGHT + cost*COST_WEIGHT

    def show_ip_route(self):
        print("Routing Table:")
        for entry in self.routing_table:
            print(dict(entry))

    def show_ip_config(self):
        print("Router ID:", self.rcid)
        print("ASN:", self.asn)
        print("IP Address:", self.ip)
        print("Port:", self.port)

    def send_rcu(self):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                while not self.shutdown_event.is_set():
                    for neighbor in self.neighbors:
                        rcu = {
                            "RCID": self.rcid,
                            "LOCAL_ASN": self.asn,
                            "Link Capacity": neighbor.capacity,
                            "Link Cost": neighbor.cost,
                            "DEST_ASN": neighbor.asn,
                            "List [DCs]": self.dcs
                        }
                        sock.sendto(json.dumps(rcu, indent=2).encode(),
                                    (neighbor.ip, neighbor.port))
                        # print(f"Sent RCU to Router {neighbor.rcid}")
                    time.sleep(10)
        except Exception as e:
            print(tb.format_exc())
            self.shutdown()

    def receive_rcu(self):  # Function to receive hello messages from neighbors
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                sock.bind((self.ip, self.port))
                while not self.shutdown_event.is_set():
                    data, addr = sock.recvfrom(1024)
                    if data.decode() == "shutdown":
                        break
                    else:
                        rcu = json.loads(data)
                        if self.show_rcu:
                            print(f"Received RCU from {addr}: {rcu['RCID']}")
        except Exception:
            print(tb.format_exc())
            self.shutdown()

    def get_input(self):
        try:
            while not self.shutdown_event.is_set():
                command = input(f"\nR{self.rcid}> ")
                if command == "show ip route":
                    self.show_ip_route()
                elif command == "show ip config":
                    self.show_ip_config()
                elif command == "help":
                    print("commands:\n")
                    print("show ip route")
                    print("show rcu")
                    print("show ip config")
                    print("shutdown")
                elif command == "show rcu":
                    self.set_show_rcu(True)
                    time.sleep(10)
                    self.set_show_rcu(False)
                elif command == "shutdown":
                    self.shutdown()
                else:
                    print("Invalid command. Please try again.")
        except Exception:
            print(tb.format_exc())
            self.shutdown()

    def start(self):  # Start router
        try:
            # Start threads for sending and receiving rcu messages
            self.send_thread = threading.Thread(target=self.send_rcu)
            self.receive_thread = threading.Thread(target=self.receive_rcu)

            self.send_thread.start()
            self.receive_thread.start()
            self.input_thread.start()

        except Exception:
            print(tb.format_exc())
            self.shutdown()

    def shutdown(self):
        print("Shutting down...")

        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.sendto("shutdown".encode(), (self.ip, self.port))

        if self.receive_thread.is_alive():
            self.receive_thread.join()

        self.shutdown_event.set()

    def __str__(self) -> str:
        router = copy.copy(self)

        dict_neighbors = []
        for n in self.neighbors:
            dict_neighbors.append(n.__dict__)

        router.neighbors = dict_neighbors

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
