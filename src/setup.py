import json
from router import Router, Neighbor


def get_num_controllers(line: str):
    num_of_controllers = int(line.strip().split(maxsplit=1)[0])
    return num_of_controllers


def create_router(filename):
    router = None

    with open(filename, 'r') as file:
        data = json.load(file)

        # Create the neighbors
        neighbors = []
        for config in list(data["neighbors"]):
            neighbors.append(Neighbor(config))

        # Create the router
        router = Router(dict(data["local"]), data["dcs"], neighbors)

    return router
