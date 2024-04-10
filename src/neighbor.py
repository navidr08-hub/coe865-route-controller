import time
import json
import threading
from router import Router, RCU_TIMER


TIMEOUT = 3  # Number of RCUs that is not received from a neighbor before setting it to down state


class Neighbor:
    def __init__(self, config: dict) -> None:
        self.rcid = config["rcid"]
        self.asn = config["asn"]
        self.ip = config["ip"]
        self.port = config["port"]
        self.capacity = config["capacity"]
        self.cost = config["cost"]

    def __str__(self) -> str:
        return json.dumps({
            "rcid": self.rcid,
            "asn": self.asn,
            "ip": self.ip,
            "port": self.port,
            "capactity": self.capacity,
            "cost": self.cost
        })


class DirectNeighbor(Neighbor):

    def __init__(self, config, neighbors: dict, dcs: list):
        super().__init__(config)
        
        self.neighbors = []
        for neighbor in neighbors:
            if not self.rcid == neighbor["rcid"]:
                self.neighbors.append(Neighbor(neighbor))
        self.dcs = dcs
        self.is_alive = False
        self.up_timer = RCU_TIMER * TIMEOUT
        self.timer_thread = None
        self.shutdown_event = threading.Event()  # Event to signal shutdown

    def timer_countdown(self):
        while (not self.shutdown_event.is_set()) and self.up_timer > 0:
            time.sleep(1)
            self.up_timer -= 1
        self.is_alive = False
        # print(f"Neighbor {self.rcid} is no longer alive.")
        self.up_timer = RCU_TIMER * TIMEOUT

    def reset(self):
        self.up_timer = RCU_TIMER * TIMEOUT

    def start(self):
        self.is_alive = True
        self.timer_thread = threading.Thread(target=self.timer_countdown)
        self.timer_thread.start()

    def shutdown(self):
        self.shutdown_event.set()

        if self.timer_thread and self.timer_thread.is_alive():
            self.timer_thread.join()

    def __str__(self) -> str:
        return json.dumps({
            "RCID": self.rcid, 
            "ASN": self.asn, 
            "PORT": self.port,
            "COST": Router.composite_cost(self.capacity, self.cost),
            "TIMER": self.up_timer,
            "NEIGHBORS": [str(neighbor) for neighbor in self.neighbors]
            }, indent=2)
