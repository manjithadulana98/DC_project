import random
import time
from ttypes import Node as BSNode
from bootstrap_server import BootstrapServerConnection
import socket
import threading
import shlex
from flask import Flask, jsonify
import hashlib
import random
import requests
import os
import traceback
import base64

app = Flask(__name__)
node_instance = None  # Will be set to the OverlayNode so Flask can access it


def load_files(file_path="file_list.txt", count=5):
    try:
        with open(file_path, "r") as f:
            all_files = list(set(line.strip() for line in f if line.strip()))
            return random.sample(all_files, min(count, len(all_files)))
    except FileNotFoundError:
        print("[Warning] file_list.txt not found. Using empty file list.")
        return []

print("[node.py] Starting up node")

class OverlayNode:
    def __init__(self, ip, port, name, bs_ip, bs_port):
        self.me = BSNode(ip, port, name)
        self.bs = BSNode(bs_ip, bs_port, "BS")
        self.routing_table = []
        self.recent_queries = set()
        self.files = load_files()
        self.search_history = {}
        self.seq_no = 0
        with open("query_list.txt", "r", encoding="utf-8") as f:
            self.query_list = [line.strip() for line in f if line.strip()]

    def assign_files(self, file_path="file_list.txt"):
        with open(file_path, "r") as f:
            file_pool = [line.strip() for line in f.readlines()]
        self.files = random.sample(file_pool, random.randint(3, 5))

    def register_and_join(self):
        self.bs_conn = BootstrapServerConnection(self.bs, self.me)
        self.users = self.bs_conn.connect_to_bs()   
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
        tokens = shlex.split(message.strip())

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
        
        elif tokens[0] == "SER":
            origin_ip = tokens[1]
            origin_port = int(tokens[2])
            filename = tokens[3].strip('"')
            ttl = int(tokens[4])

            query_key = f"{origin_ip}:{origin_port}:{filename}"
            if query_key in self.recent_queries:
                return  # Skip duplicate queries

            self.recent_queries.add(query_key)

            matched_files = [f for f in self.files if filename.lower() in f.lower()]
            if matched_files:
                hop_count = 5 - ttl
                reply = f'SEROK {len(matched_files)} {self.me.ip} {self.me.port} {hop_count} ' + " ".join(matched_files)
                self.send_udp_message(reply, (origin_ip, origin_port))
                print(f"[{self.me.name}] Found match for '{filename}', sending SEROK")
            elif ttl > 0:
                for neighbor in self.routing_table:
                    if isinstance(neighbor, tuple):
                        forward_addr = neighbor
                    else:
                        forward_addr = (neighbor.ip, neighbor.port)
                    self.send_udp_message(
                        f'SER {origin_ip} {origin_port} "{filename}" {ttl - 1}',
                        forward_addr
                    )
        
        elif tokens[0] == "SEROK":
            try:
                result_count = int(tokens[1])
                sender_ip = tokens[2]
                sender_port = int(tokens[3])
                hop_count = tokens[4]
                matched_files = tokens[5:]

                print(f"[{self.me.name}] SEROK from {sender_ip}:{sender_port} with {result_count} result(s):")
                for f in matched_files:
                    print(f" - {f}")

                # Download first file using REST
                file_to_download = matched_files[0]
                rest_port = int(sender_port) + 1000
                url = f"http://{sender_ip}:{rest_port}/download/{file_to_download}"

                response = requests.get(url)
                if response.status_code == 200:
                    data = response.json()
                    filename = data['filename']
                    file_content = data['content']  # assuming raw text or base64
                    file_size = data['size_MB']
                    file_hash = data['hash']

                    # Create a folder for the node if it doesn't exist
                    download_dir = f"downloads/{self.me.name}"
                    os.makedirs(download_dir, exist_ok=True)

                    # Save file
                    file_path = os.path.join(download_dir, filename)
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(file_content)

                    print(f"[{self.me.name}] ✔ Saved to {file_path} | {file_size}MB | SHA: {file_hash}")
                else:
                    print(f"[{self.me.name}] ✖ Download failed from {url}")

            except Exception as e:
                print(f"[{self.me.name}] ❌ Error parsing SEROK: {e}")
                traceback.print_exc()

    def send_join_requests(self):
        for peer in self.users:
            print(f"[{self.me.name}] Sending JOIN to {peer.ip}:{peer.port}")
            message = f"JOIN {self.me.ip} {self.me.port}"
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.sendto(message.encode(), (peer.ip, peer.port))
            s.close()
    
    def initiate_search(self, keyword):
        self.seq_no += 1
        self.search_history[(self.me.name, self.seq_no)] = time.time()
        
        for neighbor in self.routing_table:
            # Handle both Node and tuple formats
            if isinstance(neighbor, tuple):
                target_ip, target_port = neighbor
            else:
                target_ip, target_port = neighbor.ip, neighbor.port

            msg = f"SER {self.me.ip} {self.me.port} \"{keyword}\" 5"
            self.send_udp_message(msg, (target_ip, target_port))

        print(f"[{self.me.name}] Search initiated for: {keyword}")

    def send_udp_message(self, message, addr):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        # Handle both Node and (ip, port) tuple
        if isinstance(addr, tuple):
            target = addr
        else:
            target = (addr.ip, addr.port)

        s.sendto(message.encode(), target)
        s.close()


    def run(self):
        print(f"[{self.me.name}] Starting up node")
        self.start_udp_listener()  # NEW LINE!
        self.register_and_join()
        self.start_rest_server()
        
        try:
            print(f"[{self.me.name}] Routing table:")
            for entry in self.routing_table:
                print(f"  -> {entry}")

            print(f"[{self.me.name}] Files:")
            for f in self.files:
                print(" -", f)

            for query in self.query_list:
                self.initiate_search(query)
                time.sleep(2)
        except KeyboardInterrupt:
            print(f"[{self.me.name}] Shutting down...")
            self.bs_conn.unreg_from_bs()
        finally:
            self.bs_conn.unreg_from_bs()
    
    def start_rest_server(self):
        from threading import Thread
        global node_instance
        node_instance = self  # So the Flask route can access the node name

        flask_thread = Thread(
            target=app.run,
            kwargs={'host': self.me.ip, 'port': self.me.port + 1000, 'debug': False, 'use_reloader': False}
        )
        flask_thread.daemon = True
        flask_thread.start()



@app.route("/download/<filename>")
def download(filename):
    size_MB = random.randint(2, 10)
    content = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=size_MB * 1024 * 1024))
    encoded_content = base64.b64encode(content.encode()).decode()
    file_hash = hashlib.sha256(content.encode()).hexdigest()

    return jsonify({
        "filename": filename,
        "content": encoded_content,  # <-- this is required by the node
        "size_MB": size_MB,
        "hash": file_hash
    })


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