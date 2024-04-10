import json
from router import Router
from neighbor import DirectNeighbor, Neighbor


def create_direct_neighbor(config: dict):
    return DirectNeighbor(config)


def create_router(filename: str, router_num: int):
    try:
        with open(filename, 'r') as file:
            data = dict(json.load(file))
            router_config = data.pop(f"{router_num}")

            # Create direct neighbors
            direct_neighbors = {}
            for direct_neighbor in router_config["neighbors"]:
                dr_rcid = direct_neighbor["rcid"]
                dr = data[f"{dr_rcid}"]
                direct_neighbors[dr_rcid] = DirectNeighbor(direct_neighbor, dr["neighbors"], dr["dcs"])
                # print(str(direct_neighbors[dr_rcid]))
                
            return Router(router_config, direct_neighbors)
    except FileNotFoundError:
        print(f"Config file ({filename}) not found.")
        
    return None
