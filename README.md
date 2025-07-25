# Distributed Overlay Network - Quick Guide

A lightweight peer-to-peer file-sharing overlay network using TCP (for bootstrap server) and UDP (for node communication).

## 🔧 How to Run

### 1. Start Bootstrap Server

# Distributed Content-Sharing Overlay Network

## Overview
This project implements a distributed content-sharing overlay using a peer-to-peer (P2P) design. Nodes register with a bootstrap server, discover neighbors, exchange messages over UDP, and search for files using flooding-based keyword search.

## Features
- Bootstrap server for node registration (`bootstrap_server_main.py`)
- Peer discovery and UDP-based communication
- Flooding search with TTL and loop prevention
- Search result response (`SEROK`)
- Configurable file and query lists

## Components

- `bootstrap_server_main.py`: Starts the central bootstrap server (TCP)
- `patched_node.py`: Launches a node and applies runtime patches to bootstrap logic
- `node.py`: Main overlay node logic (executed by `patched_node.py`)
- `ttypes.py`: Defines the `Node` class used for node representation
- `file_list.txt`: List of files available at each node
- `query_list.txt`: List of search queries to simulate

## Usage

### 1. Start Bootstrap Server

```bash
python bootstrap_server_main.py
```

### 2. Launch Nodes

In separate terminals:

```bash
python patched_node.py <name> <port> <bs_ip>
```

Example:

```bash
python patched_node.py A 5101 127.0.0.1
```

## ✅ Features (Phase 1)

- Bootstrap registration via TCP
- JOIN and JOINOK via UDP
- Routing table and file list display
- File preload via `files.txt`

## 📦 Next (Phase 2)

- SER/SEROK support for search
- TTL, hops, deduplication
- Search performance logging

## 📂 Structure

```
bootstrap_server_main.py
bootstrap_server.py
patched_node.py
node.py
ttypes.py
files.txt
```

### 2. Start Nodes (in separate terminals)
```bash
python patched_node.py <NodeName> <Port> <IP>
# Example:
python patched_node.py A 5101 127.0.0.1
python patched_node.py B 5102 127.0.0.1
```

### 3. Node Behavior
- Loads files from `file_list.txt`
- Registers with the bootstrap server and discovers neighbors
- Sends JOIN messages to discovered neighbors
- Processes search queries from `query_list.txt`
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

## Notes
- Uses only Python standard libraries
- No external P2P libraries required
- Run each node in a separate terminal
- `patched_node.py` applies necessary runtime patches for compatibility with the bootstrap