import subprocess
import time
import sys
import random
import os

bs_ip = "127.0.0.1"
base_port = 5001
num_nodes = 10
node_procs = []

# 1. Pick 3 random nodes to issue queries
query_nodes = random.sample(range(1, num_nodes+1), 3)
print(f"[Main] Nodes issuing queries: {query_nodes}")

# 2. Load queries
with open("query_list.txt", "r", encoding="utf-8") as qf:
    queries = [line.strip() for line in qf if line.strip()]

# 3. Create query_list_X.txt for each node (real or empty)
for i in range(1,num_nodes+1):
    filename = f"query_list_{i}.txt"
    with open(filename, "w", encoding="utf-8") as f:
        if i in query_nodes:
            for q in queries:
                f.write(q + "\n")
        # else: write nothing (empty file)

# 4. Launch all nodes with their respective query file
for i in range(num_nodes):
    username = f"user{i + 1}"
    port = base_port + i
    query_file = f"query_list_{i+1}.txt"

    proc = subprocess.Popen([
        sys.executable, "node.py", username, str(port), bs_ip, query_file
    ])

    node_procs.append(proc)
    time.sleep(1)  # optional delay

print("[Main] All nodes launched and query files assigned.")

# 5. Wait for execution
time.sleep(40)  # long enough for queries + SEROKs

print("[Main] Metrics collection complete. Check *_metrics.csv files.")


