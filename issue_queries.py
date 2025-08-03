# issue_queries.py
import socket
import time
import random

queries = [
    "Lord", "Ring", "Lord of the rings", "Twilight", "Jack and Jill",
    "Happy Feet", "Super Mario", "Windows", "Mission Impossible", "Gaga",
    "Harry Potter", "Vampire", "American Pickers", "Tintin"
]

# Node list: IP + port
all_nodes = [("127.0.0.1", 5001 + i) for i in range(10)]
selected_nodes = random.sample(all_nodes, 3)  # Pick 3 random nodes

def send_udp(ip, port, message):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(message.encode(), (ip, port))
    sock.close()

print("Selected nodes for querying:")
for ip, port in selected_nodes:
    print(f" → {ip}:{port}")

for ip, port in selected_nodes:
    for q in queries:
        msg = f'SER {ip} {port} "{q}" 5'
        send_udp(ip, port, msg)
        print(f"[Query] Sent '{q}' to {ip}:{port}")
        time.sleep(1)  # slight delay between queries
