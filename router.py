class Router:

    def __init__(self, config: dict, dcs):
        self.rcid = config["rcid"]
        self.asn = config["asn"]
        self.ip = config["ip"]
        self.port = config["port"]
        self.dcs = dcs

    def set_links(self, links):
        self.links = links


class Link(Router):

    def __init__(self, config: dict, links, capacity, cost, dcs):
        super.__init__(params, ip, links, dcs)
        self.capacity = capacity
        self.cost = cost


class DataCenter():

    def __init__(self, params):
        self.dc_id = params[0]
        self.link_capacity = params[1]
        self.link_cost = params[2]