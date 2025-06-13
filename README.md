# Distributed Overlay Network - Quick Guide

A lightweight peer-to-peer file-sharing overlay network using TCP (for bootstrap server) and UDP (for node communication).

## 🔧 How to Run

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
