import sys
import socket
import time
from bootstrap_server import BootstrapServerConnection, Node

class LeavingNode:
    def __init__(self, ip, port, name, bs_ip, bs_port=5000):
        self.me = Node(ip, port, name)
        self.bs = Node(bs_ip, bs_port, "BS")
        self.bs_conn = BootstrapServerConnection(self.bs, self.me)
        self.routing_table = []

    def send_udp_message(self, message, address):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.sendto(message.encode(), address)
        sock.close()

    def connect_and_fetch_neighbors(self):
        try:
            self.routing_table = self.bs_conn.connect_to_bs()
        except Exception as e:
            print(f"[{self.me.name}] Error fetching neighbors: {e}")

    def leave(self):
        print(f"[{self.me.name}] Gracefully leaving the network...")

        for neighbor in self.routing_table:
            leave_msg = f"LEAVE {self.me.ip} {self.me.port} {self.me.name}"
            print(f"[{self.me.name}] Sending LEAVE to {neighbor.ip}:{neighbor.port}")
            self.send_udp_message(leave_msg, (neighbor.ip, neighbor.port))
            time.sleep(0.2)

        try:
            self.bs_conn.unreg_from_bs()
            print(f"[{self.me.name}] Successfully unregistered from BS.")
        except Exception as e:
            print(f"[{self.me.name}] Failed to unregister from BS: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python node_leave.py <username> <port> <bs_ip>")
        sys.exit(1)

    username = sys.argv[1]
    port = int(sys.argv[2])
    bs_ip = sys.argv[3]

    node = LeavingNode("127.0.0.1", port, username, bs_ip)
    node.connect_and_fetch_neighbors()
    node.leave()
