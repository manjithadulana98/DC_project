import socket
import sys
import bootstrap_server

print("[Patch] Applying patches to bootstrap_server.py...")

# --- Patch 1: Ensure message_with_length returns bytes ---
original_format = bootstrap_server.BootstrapServerConnection.message_with_length
def patched_format(self, message):
    return original_format(self, message).encode()
bootstrap_server.BootstrapServerConnection.message_with_length = patched_format

# --- Patch 2: Prevent unregister on connect ---
def fake_unreg_from_bs(self):
    print(f"[Patch] Skipping unreg_from_bs for {self.me.name}")
bootstrap_server.BootstrapServerConnection.unreg_from_bs = fake_unreg_from_bs

# --- Patch 3: Fix connect_to_bs to handle REGOK 0 properly ---
def safe_connect_to_bs(self):
    # Do not call unreg_from_bs here!
    buffer_size = 1024
    message = "REG " + self.me.ip + " " + str(self.me.port) + " " + self.me.name

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((self.bs.ip, self.bs.port))
    s.send(self.message_with_length(message))
    data = s.recv(buffer_size)
    s.close()
    print(data)

    toks = data.decode().split()
    if toks[1] != "REGOK":
        raise RuntimeError("Registration failed")

    code = int(toks[2])
    if code == 9999:
        raise RuntimeError("Bootstrap server error: command not recognized")
    elif code == 9998:
        raise RuntimeError("Registration failed: already registered or invalid IP/port/username")
    elif code == 9997:
        raise RuntimeError("Registration failed: already registered")
    elif code == 9996:
        raise RuntimeError("Bootstrap server full")

    num = int(toks[2])
    if num == 0:
        return []
    elif num == 1:
        return [bootstrap_server.Node(toks[3], int(toks[4]), toks[5])]
    else:
        l = list(range(1, num + 1))
        from random import shuffle
        shuffle(l)
        return [
            bootstrap_server.Node(toks[l[0]*3], int(toks[l[0]*3+1]), toks[l[0]*3+2]),
            bootstrap_server.Node(toks[l[1]*3], int(toks[l[1]*3+1]), toks[l[1]*3+2])
        ]

bootstrap_server.BootstrapServerConnection.connect_to_bs = safe_connect_to_bs

print("[Patch] Done. Launching node.py...\n")

# --- Execute node.py manually (preserves sys.argv) ---
with open("node.py", "r") as f:
    code = f.read()

exec(code)
