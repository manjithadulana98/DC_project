import subprocess
import time
import sys
import os
import random

bs_ip = "127.0.0.1"
base_port = 5001
num_nodes = 10

query_nodes = [2, 9, 10]  # Replace with actual values used before

eligible_nodes = list(set(range(num_nodes)) - set(query_nodes))
leave_nodes = random.sample(eligible_nodes, 2)
print(f"[Post] Nodes selected for graceful departure: {leave_nodes}")

for i in leave_nodes:
    username = f"user{i+1}"
    port = base_port + i
    print(f"[Post] Asking node {username} to leave...")

    subprocess.Popen([sys.executable, "node_leave.py", username, str(port), bs_ip])
    time.sleep(5)

print(f"[Post] Relaunching original query nodes for post-departure queries: {query_nodes}")
for i in query_nodes:
    username = f"user{i+1}"
    port = base_port + i
    query_file = f"query_list_{i}.txt"

    if not os.path.exists(query_file):
        print(f"[ERROR] Missing query file: {query_file}")
        continue

    subprocess.Popen([sys.executable, "node.py", username, str(port), bs_ip, query_file, "after"])
    time.sleep(2)

print("[Post] Waiting for re-issued queries to complete...")
time.sleep(40)

print("[Post] Done. Check *_metrics_after.csv files for results.")
