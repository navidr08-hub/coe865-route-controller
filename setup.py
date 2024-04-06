from router import Router, Link

IP = "localhost"


def get_num_controllers(line: str):
    num_of_controllers = int(line.strip().split(maxsplit=1)[0])
    return num_of_controllers


def create_router(filename):

    with open(filename, 'r') as file:
        lines = list(file)

        router_params = lines[0].strip().split()
        router = Router(router_params, IP, )
        
        links = []
        num_of_controllers = get_num_controllers(lines[1])

        for i in range (2, num_of_controllers+2):
            params = lines[i].strip().split(maxsplit=5).pop()
            capacity = params.pop(2)
            cost = params.pop(3)
            links.append(Link(params, IP, ))
            # links.append(Link(rcid=params[0], ip=IP, asn=params[1], port=params[2]))


        

def main():
    # Example usage:
    filename = 'conf.txt'  # Change this to the path of your config file
    parsed_data = create_router(filename)
    # print(parsed_data)


if __name__ == "__main__":
    main()