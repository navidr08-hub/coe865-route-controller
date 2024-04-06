import time


class RouterControl:
    def __init__(self):
        self.routers = [None] * 4
        self.sourceArray = [0] * 4
        self.destArray = [0] * 4
        self.pathArray = [0] * 10
        self.costArray = [0] * 10
        self.bwArray = [0] * 10
        self.source = 0
        self.dest = 0

    def main(self):
        print("Create Routers:")
        self.create_routers()
        print("Display Routers:")
        self.display_routers()
        self.source = int(input("Please enter your source: "))
        self.dest = int(input("Please enter your destination: "))
        print(f"The source client is: ASN{self.source}")
        print(f"The destination client is: ASN{self.dest}")

        while True:
            print("Seeking source and destination client:")
            self.find_from_to()
            print("Finding Paths...")
            self.find_path()
            print("Choosing Best Path...")
            self.find_best_path()
            time.sleep(180)
            print("Recomputing Path...")

    def create_routers(self):
        self.routers[0] = RController(1, "10.1.1.1", 10, 20, 1, 2, 2, 3, 0, 1, 1, 0, 3, 3, 3)
        self.routers[1] = RController(2, "10.1.1.2", 10, 40, 1, 4, 1, 3, 4, 1, 1, 1, 3, 3, 3)
        self.routers[2] = RController(3, "10.1.1.3", 10, 30, 1, 3, 1, 2, 4, 1, 1, 1, 3, 3, 3)
        self.routers[3] = RController(4, "10.1.1.4", 20, 30, 2, 3, 2, 3, 0, 1, 1, 0, 3, 3, 3)

    def display_routers(self):
        for r in self.routers:
            print(f"Ip: {r.ip} RCID: {r.rcid} ASN1: {r.asn1} ASN1 Cost: {r.cost1} ASN2: {r.asn2} ASN2 Cost: {r.cost2} Interface 1: RC{r.port1} Interface 2: RC{r.port2}")

    def find_from_to(self):
        for i in range(4):
            self.sourceArray[i] = 1 if self.routers[i].asn1 == self.source or self.routers[i].asn2 == self.source else 0
        for i in range(4):
            self.destArray[i] = 1 if self.routers[i].asn1 == self.dest or self.routers[i].asn2 == self.dest else 0

    def find_path(self):
        k = 0
        for i in range(4):
            if self.sourceArray[i] == 1:
                sLocalCost = self.routers[i].cost1 if self.routers[i].asn1 == self.source else self.routers[i].cost2
                for j in range(4):
                    if self.destArray[j] == 1:
                        dLocalCost = self.routers[j].cost1 if self.routers[j].asn1 == self.dest else self.routers[j].cost2
                        if self.routers[i].port1 == j + 1:
                            self.pathArray[k] = (self.routers[i].rcid * 10) + (self.routers[j].rcid)
                            self.costArray[k] = self.routers[i].intCost1 + sLocalCost + dLocalCost
                            self.bwArray[k] = min(self.routers[i].bw1, self.routers[j].bw1)
                        elif self.routers[i].port2 == j + 1:
                            self.pathArray[k] = (self.routers[i].rcid * 10) + (self.routers[j].rcid)
                            self.costArray[k] = self.routers[i].intCost2 + sLocalCost + dLocalCost
                            self.bwArray[k] = min(self.routers[i].bw2, self.routers[j].bw1)
                        else:
                            self.pathArray[k] = (self.routers[i].rcid * 10) + (self.routers[j].rcid)
                            self.costArray[k] = self.routers[i].intCost3 + sLocalCost + dLocalCost
                            self.bwArray[k] = min(self.routers[i].bw3, self.routers[j].bw1)
                        k += 1

    def find_best_path(self):
        bestPath = 0
        bestCost = 1000
        bestBW = 0
        for i in range(10):
            if self.pathArray[i] != 0:
                if self.costArray[i] < bestCost:
                    bestPath = self.pathArray[i]
                    bestCost = self.costArray[i]
                    bestBW = self.bwArray[i]
        print(f"Best Path: {bestPath}, Cost: {bestCost}, Bandwidth: {bestBW}")


if __name__ == "__main__":
    rc = RouterControl()
    rc.main()