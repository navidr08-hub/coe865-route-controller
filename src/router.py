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

    def __init__(self, config: dict, neighbors: dict):
        self.rcid = config["local"]["rcid"]
        self.asn = config["local"]["asn"]
        self.ip = config["local"]["ip"]
        self.port = config["local"]["port"]
        self.dcs = config["dcs"]
        self.neighbors = neighbors
        self.rcu_buffer = deque(maxlen=MAX_BUFFER_SIZE)
        self.watch_rcu = False
        self.shutdown_event = threading.Event()  # Event to signal shutdown
        self.input_thread = threading.Thread(target=self.get_input)
        self.routing_table = []

    def set_watch_rcu(self, value: bool):
        self.watch_rcu = value

    def get_rcus(self, num):
        buffer_len = len(self.rcu_buffer)
        if num > MAX_BUFFER_SIZE:
            print(
                f"Number of rcus requested exceeds buffer size ({MAX_BUFFER_SIZE}).")
        elif num > buffer_len:
            print("Not enough rcus collected yet. See the latest below.")
            return list(self.rcu_buffer)
        else:
            return list(self.rcu_buffer)[-num:]

        return None

    @staticmethod
    def composite_cost(capacity, cost):
        return capacity*CAPACITY_WEIGHT + cost*COST_WEIGHT
    
    def calculate_total_cost(self, path):
        total_cost = 0
        for i in range(len(path) - 1):
            current_rcid = path[i]
            if current_rcid == self.rcid:
                continue
            neighbor = self.neighbors[current_rcid]
            # Find the cost of the link between current router and its neighbor
            total_cost += self.composite_cost(neighbor.capacity, neighbor.cost)
        return total_cost

    def get_all_paths(self, src_rcid, dest_rcid, visited=None, path=None):
        if visited is None:
            visited = set()
        if path is None:
            path = []

        visited.add(src_rcid)
        path = path + [src_rcid]

        if src_rcid == dest_rcid:
            return [path]

        paths = []
        for neighbor in self.neighbors.values():
            if neighbor.is_alive and neighbor.rcid not in visited:
                new_paths = self.get_all_paths(neighbor.rcid, dest_rcid, visited, path)
                for new_path in new_paths:
                    paths.append(new_path)

        visited.remove(src_rcid)

        return paths
    
    def get_optimal_path(self, src_rcid, dest_rcid):
        paths = self.get_all_paths(src_rcid, dest_rcid)
        
        if not paths:
            return None

        optimal_path = paths[0]
        min_cost = float('inf')

        for path in paths:
            total_cost = self.calculate_total_cost(path)  # Implement this function to calculate the total cost of a path
            if total_cost < min_cost:
                min_cost = total_cost
                optimal_path = path

        return optimal_path, min_cost
    
    def purge_dead_routes(self):
        for neighbor in self.neighbors.values():
            if not neighbor.is_alive:
                for i, route in enumerate(self.routing_table):
                    path = list(route["path"])
                    if neighbor.rcid in path:
                        self.routing_table.pop(i)

    def update_routing_table(self, rcu):
        rcid = rcu["RCID"]
        # port = rcu["PORT"]
        # local_asn = rcu["LOCAL_ASN"]
        # link_capacity = rcu["Link Capacity"]
        # link_cost = rcu["Link Cost"]
        # dest_asn = rcu["DEST_ASN"]
        # local_dcs = rcu["List [DCs]"]

        self.rcu_buffer.append(rcu)

        if self.watch_rcu:
            print(f"Received RCU from {rcid}")

        # Check neighbors
        if not self.neighbors[rcid].is_alive:
            self.neighbors[rcid].start()
        else:
            self.neighbors[rcid].reset()

        self.purge_dead_routes()

        for neighbor in self.neighbors.values():
            if neighbor.is_alive:
                path, cost = self.get_optimal_path(self.rcid, rcid)
                for route in self.routing_table:
                    if route["asn"] == neighbor.asn:
                        if cost > int(route["cost"]):
                            route["cost"] = cost
                            route["path"] = path

                        return
                    
                route = {"asn": neighbor.asn, "path": path, "cost": cost}
                self.routing_table.append(route)

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

    def show_neighbors(self):
        for neighbor in self.neighbors.values():
            if neighbor.is_alive:
                print(str(neighbor))

    def show_paths(self):
        for neighbor in self.neighbors.values():
            if neighbor.is_alive:
                print(str(self.get_all_paths(self.rcid, neighbor.rcid)))

    def send_rcu(self):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                while not self.shutdown_event.is_set():
                    for neighbor in self.neighbors.values():
                        rcu = {
                            "RCID": self.rcid,
                            "PORT": self.port,
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
            print("Shutting down, please enter any key...")
            self.shutdown()

    def receive_rcu(self):  # Function to receive hello messages from neighbors
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                sock.bind((self.ip, self.port))
                sock.settimeout(1)  # Set a timeout of 1 second
                while not self.shutdown_event.is_set():
                    try:
                        data, _ = sock.recvfrom(1024)
                        if data.decode() == "shutdown":
                            break
                        else:
                            rcu = json.loads(data)
                            self.update_routing_table(rcu)
                    except socket.timeout:
                        pass  # Continue listening if no data received within the timeout
        except Exception:
            print(tb.format_exc())
            print("Shutting down, please enter any key...")
            self.shutdown()

    def get_input(self):
        try:
            while not self.shutdown_event.is_set():
                command = input(f"\nR{self.rcid}> ")

                if command == "help":
                    print("commands:\n")
                    print(" - show ip route")
                    print(" - show ip config")
                    print(" - watch ip rcu [# of rcu]")
                    print(" - show ip rcu [# of rcu]")
                    print(" - show ip neighbor")
                    print(" - show paths")
                    print(" - shutdown")
                elif command == "show ip route":
                    self.show_ip_route()
                elif command == "show ip config":
                    self.show_ip_config()
                elif command.startswith("watch ip rcu "):
                    self.watch_rcus(command)
                elif command.startswith("show ip rcu "):
                    self.show_rcus(command)
                elif command == "show ip neighbor":
                    self.show_neighbors()
                elif command == "show paths":
                    self.show_paths()
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

        for neighbor in self.neighbors.values():
            neighbor.shutdown()

        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.sendto("shutdown".encode(), (self.ip, self.port))

        if self.receive_thread.is_alive():
            self.receive_thread.join()

        self.shutdown_event.set()

    def __str__(self) -> str:
        router = copy.copy(self)

        dict_neighbors = []
        for n in self.neighbors.values():
            dict_neighbors.append(n.__dict__)

        router.neighbors = dict_neighbors

        return json.dumps(router.__dict__, indent=2)
