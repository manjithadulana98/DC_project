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
import csv

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
    def __init__(self, ip, port, name, bs_ip, bs_port, query_file=None):
        self.me = BSNode(ip, port, name)
        self.bs = BSNode(bs_ip, bs_port, "BS")
        self.routing_table = []
        self.recent_queries = set()
        self.files = load_files()
        self.search_history = {}
        self.seq_no = 0
        # with open("query_list.txt", "r", encoding="utf-8") as f:
        #     self.query_list = [line.strip() for line in f if line.strip()]

        self.query_list = []
        if query_file and os.path.exists(query_file):
            with open(query_file, "r", encoding="utf-8") as f:
                self.query_list = [line.strip() for line in f if line.strip()]

        self.metrics = {
            "sent_SER": 0,
            "received_SER": 0,
            "received_SEROK": 0,
            "successes": 0,
            "total_latency": 0.0000,
            "total_hops": 0,
            "queries": 0
        }
        self.search_timestamps = {}  # (ip, port, filename) →

        self.message_stats = {
            "received_SER": 0,
            "forwarded_SER": 0,
            "answered_SER": 0,
            "received_SEROK": 0,
        }
        self.query_results = []  # (query, found, hops, latency)
        self.query_start_time = {}  # key = (ip, port, query)

    def assign_files(self, file_path="file_list.txt"):
        with open(file_path, "r") as f:
            file_pool = [line.strip() for line in f.readlines()]
        self.files = random.sample(file_pool, random.randint(3, 5))


    def register_and_join(self):
        self.bs_conn = BootstrapServerConnection(self.bs, self.me)
        try:
            self.users = self.bs_conn.connect_to_bs()
        except RuntimeError as e:
            print(f"[{self.me.name}] Registration failed: {e}")
            return  # Exit early, do not run/join/listen

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
            self.message_stats["received_SER"] += 1
            origin_ip = tokens[1]
            origin_port = int(tokens[2])
            filename = tokens[3].strip('"')
            ttl = int(tokens[4])
            query_key = f"{origin_ip}:{origin_port}:{filename}"

            if query_key in self.recent_queries:
                return

            self.recent_queries.add(query_key)
            matched_files = [f for f in self.files if filename.lower() in f.lower()]

            if matched_files:
                reply = f"SEROK {len(matched_files)} {self.me.ip} {self.me.port} {5 - ttl} " + " ".join(matched_files)
                self.send_udp_message(reply, (origin_ip, origin_port))
                self.message_stats["answered_SER"] += 1
            elif ttl > 0:
                self.message_stats["forwarded_SER"] += 1
                for neighbor in self.routing_table:
                    self.send_udp_message(
                        f'SER {origin_ip} {origin_port} "{filename}" {ttl - 1}',
                        (neighbor[0], neighbor[1])
                    )

        elif tokens[0] == "SEROK":
            self.message_stats["received_SEROK"] += 1
            ip = tokens[2]
            port = tokens[3]
            hops = int(tokens[4])
            filename = " ".join(tokens[5:])
            key = f"{ip}:{port}:{filename}"

            latency = time.time() - self.query_start_time.get((ip, port, filename), time.time())
            print(time.time())
            print(self.query_start_time.get((ip, port, filename), time.time()))
            print(latency)
            self.query_results.append((filename, True, hops, latency))
            print(f"[{self.me.name}] → Found '{filename}' in {hops} hops, latency {latency:.5f}s")

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
        self.metrics["sent_SER"] += len(self.routing_table)
        self.metrics["queries"] += 1
        self.search_timestamps[(self.me.ip, self.me.port, keyword.lower())] = time.time()

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

    def save_metrics(self):
        if any("after" in arg.lower() for arg in sys.argv):
            suffix = "metrics_after"
        else:
            suffix = "metrics"
        filename = f"{self.me.name}_{suffix}.csv"
        with open(filename, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Query", "Found", "Hops", "Latency"])
            for q in self.query_results:
                writer.writerow(q)
            writer.writerow([])
            writer.writerow(["Metric", "Count"])
            for key, val in self.message_stats.items():
                writer.writerow([key, val])
            writer.writerow(["Routing Table Size", len(self.routing_table)])

    def graceful_leave(self):
        print(f"[{self.me.name}] Initiating graceful leave...")

        # 1. Notify all neighbors
        for neighbor in self.routing_table:
            leave_msg = f"LEAVE {self.me.ip} {self.me.port}"
            self.send_udp_message(leave_msg, (neighbor.ip, neighbor.port))
            print(f"[{self.me.name}] Sent LEAVE to {neighbor.name}")

        time.sleep(1)  # small delay for messages to propagate

        # 2. UNREG from Bootstrap Server
        try:
            self.bs_conn.unreg_from_bs()
            print(f"[{self.me.name}] Successfully unregistered from BS.")
        except RuntimeError as e:
            print(f"[{self.me.name}] UNREG failed: {e}")

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
                time.sleep(5)

            time.sleep(20)  # allow time for SEROKs to arrive
            self.show_metrics()
            self.save_metrics()
            print(f"[{self.me.name}] All queries completed.")
        except KeyboardInterrupt:
            print(f"[{self.me.name}] Shutting down...")
            self.bs_conn.unreg_from_bs()
        # finally:
        #     self.bs_conn.unreg_from_bs()
        finally:
            self.save_metrics()  # <-- ensure it's saved even on failure
            try:
                self.bs_conn.unreg_from_bs()
            except Exception as e:
                print(f"[{self.me.name}] Unregister failed: {e}")

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

    def show_metrics(self):
        print("\n--- Performance Metrics ---")
        success_rate = self.metrics["successes"] / self.metrics["queries"] * 100 if self.metrics["queries"] > 0 else 0
        avg_hops = self.metrics["total_hops"] / self.metrics["successes"] if self.metrics["successes"] > 0 else 0
        avg_latency = self.metrics["total_latency"] / self.metrics["successes"] if self.metrics["successes"] > 0 else 0
        print(f"Search Success Rate: {success_rate:.2f}%")
        print(f"Average Hop Count: {avg_hops:.2f}")
        print(f"Average Latency: {avg_latency:.2f} sec")
        print(f"Message Overhead (SER): {self.metrics['sent_SER']}")
        print(f"Message Overhead (SEROK): {self.metrics['received_SEROK']}")


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
    if len(sys.argv) < 4:
        print("Usage: python node.py <username> <port> <bs_ip> [query_file]")
        sys.exit(1)

    name = sys.argv[1]
    port = int(sys.argv[2])
    bs_ip = sys.argv[3]
    # query_file = sys.argv[4] if len(sys.argv) > 4 else None
    query_file = sys.argv[4]

    node = OverlayNode("127.0.0.1", port, name, bs_ip, 5000, query_file)
    node.run()
