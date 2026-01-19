# Part 2 — How to Run (TCP Chat App)

## 1) Overview
This is a **Client–Server** chat application over **TCP sockets**.
- Each client connects to the server and identifies with a unique username (`HELLO <username>`).
- The server supports **private 1-to-1 chats** (not group chat) using `CHAT <user>`.
- Messages are sent only to the selected chat partner using `MSG <text>`.
- The server supports **at least 5 concurrent clients**.

## 2) Project Structure
Inside `part_2/`:
- `server.py` — TCP server (listens and manages clients + private chats)
- `client.py` — CLI client (text-based)
- `protocol.py` — command parsing helper
- `schema.sql` — database schema file (included as required output)

---

## 3) Installation & Run Instructions (macOS)

### Step 1 — Open terminal and go to `part_2`
From your project root:
```bash
cd part_2
```

### Step 2 — Activate the virtual environment
If your `.venv` is in the **project root**, run:
```bash
source ../.venv/bin/activate
```

### Step 3 — Start the server (Terminal 1)
```bash
python3 server.py
```

You should see something like:
```bash
[SERVER] Listening on ('127.0.0.1', 12345)
```

### Step 4 — Start clients (Terminal 2, 3, 4, …)
Open a new terminal for each client and run:
```bash
cd part_2
source ../.venv/bin/activate   
python3 client.py
```
