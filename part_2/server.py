import asyncio
from typing import Dict, Optional, Tuple
from protocol import parse_line

HOST = "127.0.0.1"
PORT = 12345

# username -> (reader, writer)
clients: Dict[str, Tuple[asyncio.StreamReader, asyncio.StreamWriter]] = {}

# username -> partner_username  (only if currently in chat)
pairs: Dict[str, str] = {}

clients_lock = asyncio.Lock()


async def send_line(writer: asyncio.StreamWriter, line: str):
    writer.write((line + "\n").encode())
    await writer.drain()


async def safe_close(writer: asyncio.StreamWriter):
    try:
        writer.close()
        await writer.wait_closed()
    except Exception:
        pass


def is_busy(username: str) -> bool:
    return username in pairs


async def disconnect_user(username: str):
    async with clients_lock:
        if username not in clients:
            return

        _, writer = clients[username]

        # If user had a partner - notify and clear pairing
        partner = pairs.get(username)
        if partner:
            pairs.pop(username, None)
            pairs.pop(partner, None)

            if partner in clients:
                _, partner_writer = clients[partner]
                await send_line(partner_writer, f"INFO peer_disconnected {username}")

        clients.pop(username, None)

    await safe_close(writer)


async def handle_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    username: Optional[str] = None

    try:
        await send_line(writer, "INFO Welcome! Please identify: HELLO <username>")

        # ---- Require HELLO first ----
        first = await reader.readline()
        if not first:
            await safe_close(writer)
            return

        msg = parse_line(first.decode(errors="ignore"))
        if msg.cmd != "HELLO" or not msg.args.strip():
            await send_line(writer, "ERR must_send_HELLO_first")
            await safe_close(writer)
            return

        requested_username = msg.args.strip()

        async with clients_lock:
            if requested_username in clients:
                await send_line(writer, "ERR username_taken")
                await safe_close(writer)
                return

            username = requested_username
            clients[username] = (reader, writer)

        await send_line(writer, "OK HELLO")
        await send_line(writer, "INFO Commands: LIST | CHAT <user> | MSG <text> | BYE")

        # ---- Main loop ----
        while True:
            raw = await reader.readline()
            if not raw:
                # unexpected disconnect
                break

            msg = parse_line(raw.decode(errors="ignore"))

            if msg.cmd == "BYE":
                await send_line(writer, "OK BYE")
                break

            elif msg.cmd == "LIST":
                async with clients_lock:
                    users = sorted(clients.keys())
                await send_line(writer, "OK USERS " + ", ".join(users))

            elif msg.cmd == "CHAT":
                target = msg.args.strip()
                if not target:
                    await send_line(writer, "ERR usage CHAT <username>")
                    continue

                async with clients_lock:
                    if target not in clients:
                        await send_line(writer, "ERR user_not_found")
                        continue
                    if target == username:
                        await send_line(writer, "ERR cannot_chat_with_yourself")
                        continue

                    # Busy checks
                    if is_busy(username):
                        await send_line(writer, "ERR you_are_already_in_chat")
                        continue
                    if is_busy(target):
                        await send_line(writer, "ERR user_busy")
                        continue

                    # Pair them
                    pairs[username] = target
                    pairs[target] = username

                    _, target_writer = clients[target]

                await send_line(writer, f"OK CONNECTED {target}")
                await send_line(target_writer, f"OK CONNECTED {username}")

            elif msg.cmd == "MSG":
                text = msg.args.strip()
                if not text:
                    await send_line(writer, "ERR empty_message")
                    continue

                async with clients_lock:
                    partner = pairs.get(username)
                    if not partner:
                        await send_line(writer, "ERR not_connected_use_CHAT")
                        continue
                    if partner not in clients:
                        await send_line(writer, "ERR partner_not_available")
                        continue

                    _, partner_writer = clients[partner]

                await send_line(partner_writer, f"FROM {username} {text}")
                await send_line(writer, "OK SENT")

            else:
                await send_line(writer, "ERR unknown_command")

    except Exception:
        # Treat any crash as disconnect
        pass
    finally:
        if username:
            await disconnect_user(username)
        else:
            await safe_close(writer)


async def main():
    server = await asyncio.start_server(handle_client, HOST, PORT)
    addrs = ", ".join(str(sock.getsockname()) for sock in server.sockets)
    print(f"[SERVER] Listening on {addrs}")

    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())