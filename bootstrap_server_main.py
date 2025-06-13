import socket
import threading

registered_nodes = []

def handle_client(conn):
    global registered_nodes
    data = conn.recv(1024).decode().strip()

    # Strip 4-digit length prefix if present
    if data[:4].isdigit() and data[4] == ' ':
        data = data[5:]  # Remove length + space
    print("[BS] Received:", data)

    if data.startswith("REG"):
        _, ip, port, username = data.split()
        node_exists = any(n["ip"] == ip and n["port"] == port for n in registered_nodes)
        if node_exists:
            response = "0025 REGOK 9998"
        else:
            registered_nodes.append({"ip": ip, "port": port, "username": username})
            peers = [n for n in registered_nodes if not (n["ip"] == ip and n["port"] == port)]
            peer_data = ""
            for peer in peers[:2]:
                peer_data += f" {peer['ip']} {peer['port']} {peer['username']}"
            count = min(len(peers), 2)
            length = 12 + len(peer_data)
            if count == 0:
                response = "0012 REGOK 0"
            else:
                response = f"{length:04} REGOK {count}{peer_data}"

    elif data.startswith("UNREG"):
        _, ip, port, username = data.split()
        before = len(registered_nodes)
        registered_nodes = [n for n in registered_nodes if not (n["ip"] == ip and n["port"] == port and n["username"] == username)]
        after = len(registered_nodes)
        if before == after:
            response = "0012 UNROK 9999"
        else:
            response = "0012 UNROK 0"

    elif data.strip() == "PRINT":
        print("[BS] Currently registered nodes:")
        for node in registered_nodes:
            print(" -", node)
        response = "0012 OKAY"

    else:
        response = "0010 ERROR"

    conn.send(response.encode())
    conn.close()

def start_server():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("0.0.0.0", 5000))
    s.listen(5)
    print("[BS] Bootstrap Server running on port 5000...")

    while True:
        conn, _ = s.accept()
        threading.Thread(target=handle_client, args=(conn,), daemon=True).start()

if __name__ == "__main__":
    start_server()
