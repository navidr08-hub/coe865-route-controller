import socket
import time

# Function to send a hello message
def send_hello(router_address, router_port):
    try:
        hello_message = "Hello from router!"
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.sendto(hello_message.encode(), (router_address, router_port))
            print("Hello message sent to", router_address)
    except Exception as e:
        print("Error:", e)

# Function to discover neighboring routers
def discover_neighbors():
    # Define the broadcast address and port
    broadcast_address = '255.255.255.255'  # Broadcast address
    broadcast_port = 12345  # Choose a port for broadcasting

    try:
        # Create a UDP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        # Send a broadcast message to discover neighboring routers
        sock.sendto(b"Hello, any routers here?", (broadcast_address, broadcast_port))

        # Receive responses (hello messages) from neighboring routers
        while True:
            data, addr = sock.recvfrom(1024)
            print(f"Received hello message from {addr}: {data.decode()}")

            # You can add further logic here to handle the received messages
            
    except Exception as e:
        print("Error:", e)
    finally:
        sock.close()

if __name__ == "__main__":
    # Start the discovery process
    discover_neighbors()
