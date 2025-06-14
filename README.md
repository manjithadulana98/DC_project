# Distributed Content-Sharing Overlay Network

## Overview
This project implements a distributed content-sharing overlay using a peer-to-peer (P2P) design. Nodes can register with a bootstrap server, discover neighbors, exchange messages over UDP, and search for files using flooding-based keyword search.

## Features
- Bootstrap server for node registration
- Peer discovery and UDP-based communication
- Flooding search with TTL and loop prevention
- Search result response (`SEROK`)
- Configurable file and query list

## Components
- `bootstrap_server_main.py`: Starts the central bootstrap server (TCP)
- `patched_node.py`: Launches a node and applies dynamic patches
- `node.py`: Main overlay node logic (called by `patched_node.py`)
- `file_list.txt`: List of files for each node
- `queries.txt`: Search queries to simulate

## Usage

### 1. Start Bootstrap Server
```bash
python bootstrap_server_main.py
```

### 2. Start Nodes (in separate terminals)

```
python patched_node.py A 5101 127.0.0.1
python patched_node.py B 5102 127.0.0.1

```

### 3. Each node:
- Loads files from file_list.txt

- Sends JOIN messages to discovered neighbors

- Processes search queries from queries.txt

- Receives SEROK responses and logs matches

## Message Formats
### Registration (TCP)

```
REG <ip> <port> <username>
```
### Join / Search (UDP)
```
JOIN <ip> <port>
SER <origin_ip> <origin_port> "<keyword>" <ttl>
SEROK <file_count> <ip> <port> <hops> <file1> <file2> ...

```
### File Sharing
- File matching is case-insensitive and partial keyword-based

- All matches are returned via SEROK

### Logging
Each node logs:

- Neighbors from bootstrap

- Incoming messages

- Search initiations

- Matches via SEROK

### Notes
- Uses only Python standard libraries

- Avoids external P2P libraries

- Be sure to run each node in a separate terminal