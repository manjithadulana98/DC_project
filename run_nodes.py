import subprocess
import time

bs_ip = "127.0.0.1"
base_port = 5001

for i in range(10):
    username = f"user{i+1}"
    port = base_port + i
    subprocess.Popen(["python", "node.py", username, str(port), bs_ip])
    time.sleep(1)