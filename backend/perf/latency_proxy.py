"""A TCP proxy that adds a fixed one-way delay, to measure the app with a real network round trip
instead of estimating it (local perf MySQL only - it listens on 127.0.0.1).

    python -m perf.latency_proxy --listen 33309 --target 127.0.0.1:33308 --one-way-ms 21

Every chunk is forwarded `one-way-ms` after it arrived, in order, in each direction - so every
statement pays one full round trip (2 x one-way) like on the managed database, while throughput is
not otherwise limited. 21 ms each way = the ~42 ms round trip measured from the dev PC to production.
Plain threads + time.sleep: on Windows, asyncio timers only tick every ~15.6 ms, time.sleep is
high-resolution.
"""

import argparse
import queue
import socket
import threading
import time


def _forward(source: socket.socket, target: socket.socket, delay: float) -> None:
    pending: queue.Queue = queue.Queue()

    def receive():
        while True:
            try:
                chunk = source.recv(65536)
            except OSError:
                chunk = b""
            pending.put((time.perf_counter() + delay, chunk))
            if not chunk:
                return

    def send():
        while True:
            due, chunk = pending.get()
            wait = due - time.perf_counter()
            if wait > 0:
                time.sleep(wait)
            if not chunk:
                try:
                    target.shutdown(socket.SHUT_WR)
                except OSError:
                    pass
                return
            try:
                target.sendall(chunk)
            except OSError:
                return

    threading.Thread(target=receive, daemon=True).start()
    threading.Thread(target=send, daemon=True).start()


def main(listen: int, target_host: str, target_port: int, delay: float) -> None:
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("127.0.0.1", listen))
    server.listen(64)
    print(f"latency proxy 127.0.0.1:{listen} -> {target_host}:{target_port}, {delay * 1000:.0f} ms each way", flush=True)
    while True:
        client, _ = server.accept()
        upstream = socket.create_connection((target_host, target_port))
        for s in (client, upstream):
            s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        _forward(client, upstream, delay)
        _forward(upstream, client, delay)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--listen", type=int, required=True)
    parser.add_argument("--target", required=True, help="host:port of the local perf MySQL")
    parser.add_argument("--one-way-ms", type=float, default=21)
    args = parser.parse_args()
    host, port = args.target.rsplit(":", 1)
    if host not in ("127.0.0.1", "localhost"):
        raise SystemExit("local perf MySQL only")
    main(args.listen, host, int(port), args.one_way_ms / 1000)
