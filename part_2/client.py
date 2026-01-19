import asyncio
import sys

HOST = "127.0.0.1"
PORT = 12345


async def read_from_server(reader: asyncio.StreamReader):
    while True:
        line = await reader.readline()
        if not line:
            print("[INFO] Server closed the connection.")
            return
        print("[SERVER]", line.decode().strip())


async def write_to_server(writer: asyncio.StreamWriter):
    loop = asyncio.get_event_loop()

    while True:
        user_input = await loop.run_in_executor(None, sys.stdin.readline)
        if not user_input:
            continue

        msg = user_input.strip()
        if not msg:
            continue

        writer.write((msg + "\n").encode())
        await writer.drain()

        if msg.upper() == "BYE":
            return


async def main():
    print(f"[CLIENT] Connecting to {HOST}:{PORT} ...")
    reader, writer = await asyncio.open_connection(HOST, PORT)

    task_read = asyncio.create_task(read_from_server(reader))
    task_write = asyncio.create_task(write_to_server(writer))

    done, pending = await asyncio.wait(
        {task_read, task_write},
        return_when=asyncio.FIRST_COMPLETED
    )

    for t in pending:
        t.cancel()

    try:
        writer.close()
        await writer.wait_closed()
    except Exception:
        pass


if __name__ == "__main__":
    asyncio.run(main())