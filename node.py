import random
import time
from ttypes import Node as BSNode
from bootstrap_server import BootstrapServerConnection
import socket
import threading


print("[node.py] Starting up node")

class OverlayNode:
    def __init__(self, ip, port, name, bs_ip, bs_port):
        self.me = BSNode(ip, port, name)
        self.bs = BSNode(bs_ip, bs_port, "BS")
        self.routing_table = []
        self.files = []

    def assign_files(self, file_path="file_list.txt"):
        with open(file_path, "r") as f:
            file_pool = [line.strip() for line in f.readlines()]
        self.files = random.sample(file_pool, random.randint(3, 5))

    def register_and_join(self):
        with BootstrapServerConnection(self.bs, self.me) as bs_conn:
            self.users = bs_conn.users  # Store initial neighbors
            print(f"[{self.me.name}] Neighbors from BS:")
            for peer in self.users:
                print(f" → {peer.ip}:{peer.port} ({peer.name})")
            
            self.send_join_requests()  # Send JOIN to each neighbor


    def display_status(self):
        print(f"\n[{self.me.name}] Files:")
        for f in self.files:
            print(f" - {f}")
    
    def start_udp_listener(self):
        def listen():
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.bind((self.me.ip, self.me.port))
            print(f"[{self.me.name}] UDP listener active on {self.me.ip}:{self.me.port}")

            while True:
                data, addr = s.recvfrom(1024)
                self.handle_udp_message(data.decode(), addr)

        threading.Thread(target=listen, daemon=True).start()

    def handle_udp_message(self, message, addr):
        print(f"[{self.me.name}] Received UDP: '{message}' from {addr}")
        tokens = message.strip().split()

        if tokens[0] == "JOIN":
            sender_ip = tokens[1]
            sender_port = int(tokens[2])

            # Add the sender to our routing table
            self.routing_table.append((sender_ip, sender_port))

            # Reply with JOINOK
            reply = "JOINOK 0"
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.sendto(reply.encode(), addr)
            s.close()

        elif tokens[0] == "JOINOK":
            if tokens[1] == "0":
                print(f"[{self.me.name}] Successfully joined with {addr}")
                self.routing_table.append(addr)

    def send_join_requests(self):
        for peer in self.users:
            print(f"[{self.me.name}] Sending JOIN to {peer.ip}:{peer.port}")
            message = f"JOIN {self.me.ip} {self.me.port}"
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.sendto(message.encode(), (peer.ip, peer.port))
            s.close()
        

    def run(self):
        print(f"[{self.me.name}] Starting up node")
        self.start_udp_listener()  # NEW LINE!
        self.register_and_join()

        print(f"[{self.me.name}] Routing table:")
        for entry in self.routing_table:
            print(f"  -> {entry}")

        print(f"[{self.me.name}] Files:")
        for f in self.files:
            print(" -", f)


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 4:
        print("Usage: python node.py <username> <port> <bs_ip>")
        sys.exit(1)

    name = sys.argv[1]
    port = int(sys.argv[2])
    bs_ip = sys.argv[3]

    node = OverlayNode("127.0.0.1", port, name, bs_ip, 5000)
    node.run()