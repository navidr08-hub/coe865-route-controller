import socket
import threading
import json
import time
import copy
import traceback as tb

from collections import deque


COST_WEIGHT = 1
CAPACITY_WEIGHT = 1
RCU_TIMER = 10
MAX_BUFFER_SIZE = 10


class Router:

    def __init__(self, config: dict, dcs: list, neighbors: list):
        self.rcid = config["rcid"]
        self.asn = config["asn"]
        self.ip = config["ip"]
        self.port = config["port"]
        self.dcs = dcs
        self.neighbors = neighbors
        self.rcu_buffer = deque(maxlen=MAX_BUFFER_SIZE)
        self.watch_rcu = False
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

    def set_watch_rcu(self, value: bool):
        self.watch_rcu = value

    def get_rcus(self, num):
        buffer_len = len(self.rcu_buffer)
        if num > MAX_BUFFER_SIZE:
            print(f"Number of rcus requested exceeds buffer size ({MAX_BUFFER_SIZE}).")
        elif num > buffer_len:
            print("Not enough rcus collected yet. See the latest below.")
            return list(self.rcu_buffer)
        else:
            return list(self.rcu_buffer)[-num:]
        
        return None

    @staticmethod
    def composite_cost(capacity, cost):
        return capacity*CAPACITY_WEIGHT + cost*COST_WEIGHT
    
    def get_rcu_port(self, rcid):
        port = 0
        for neighbor in self.neighbors:
            if neighbor.rcid == rcid:
                port = neighbor.port

        if port == 0:
            raise Exception("Neighbor was not found... Bug found.")
        else:
            return port 
    
    def update_routing_table(self, rcu):
        rcid = rcu["RCID"]
        dest_asn = rcu["DEST_ASN"]
        link_capacity = rcu["Link Capacity"]
        link_cost = rcu["Link Cost"]
        local_dcs = rcu["List [DCs]"]
        port = self.get_rcu_port(rcid)

        # Check if the destination ASN already exists in the routing table
        for entry in self.routing_table:
            if entry["asn"] == dest_asn:
                # Update the entry if a better path is found
                new_cost = self.composite_cost(link_capacity, link_cost)
                for dc in local_dcs:
                    dc_cost = self.composite_cost(dc["capacity"], dc["cost"])
                    total_cost = new_cost + dc_cost
                    if total_cost < entry["cost"]:
                        entry["next_hop"] = rcid
                        entry["interface"] = port
                        entry["cost"] = total_cost
                return

        # If the destination ASN is not in the routing table, add it
        new_entry = {
            "asn": dest_asn,
            "next_hop": rcid,
            "interface": port,
            "cost": float('inf')  # Set to infinity for now
        }
        for dc in local_dcs:
            dc_cost = self.composite_cost(dc["capacity"], dc["cost"])
            total_cost = self.composite_cost(link_capacity, link_cost) + dc_cost
            if total_cost < new_entry["cost"]:
                new_entry["cost"] = total_cost
        self.routing_table.append(new_entry)

    def show_ip_route(self):
        print("Routing Table:")
        for entry in self.routing_table:
            print(dict(entry))

    def show_ip_config(self):
        print("Router ID:", self.rcid)
        print("ASN:", self.asn)
        print("IP Address:", self.ip)
        print("Port:", self.port)

    def watch_rcus(self, command):
        try:
            duration = int(command.split()[-1]) * RCU_TIMER + RCU_TIMER/2
            self.set_watch_rcu(True)
            time.sleep(duration)
            self.set_watch_rcu(False)
        except ValueError:
            print("Not an integer. Please enter an integer.")
            print("example: watch rcu 1")

    def show_rcus(self, command):
        try:
            num = int(command.split()[-1])
            rcus = self.get_rcus(num)
            if rcus:
                print(f"{num} rcus in buffer\n_______________________")
                for rcu in rcus:
                    print(rcu)
        except ValueError:
            print("Not an integer. Please enter an integer.")
            print("example: show rcu 1")

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
                    time.sleep(RCU_TIMER)
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
                        if self.watch_rcu:
                            print(f"Received RCU from {addr}: {rcu['RCID']}")

                        self.update_routing_table(rcu)
        except Exception:
            print(tb.format_exc())
            print("Shutting down, please enter any key...")
            self.shutdown_event.set()

    def get_input(self):
        try:
            while not self.shutdown_event.is_set():
                command = input(f"\nR{self.rcid}> ")

                if command == "help":
                    print("commands:\n")
                    print("show ip route")
                    print("watch rcu [# of rcu]")
                    print("show rcu [# of rcu]")
                    print("show ip config")
                    print("shutdown")
                elif command == "show ip route":
                    self.show_ip_route()
                elif command == "show ip config":
                    self.show_ip_config()
                elif command.startswith("watch rcu "):
                    self.watch_rcus(command)
                elif command.startswith("show rcu "):
                    self.show_rcus(command)
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
