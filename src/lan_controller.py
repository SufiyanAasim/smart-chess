# ==============================================================================
# Project: Smart Chess
# Module: LAN Controller (Socket Networking & Multi-threaded UDP/TCP loops)
# Author: Taha Siddiqui (@13eeCoder) - Security & Networking, Multi-threading
# License: MIT License
# ==============================================================================
__author__ = "Taha Siddiqui"

import queue
import socket
import threading
import chess

from network import get_local_ip


PORT = 5000


class _LanServer:
    """
    Internal multi-threaded TCP server for LAN room synchronization (@author: Taha Siddiqui).
    Manages thread locks, client sockets, and move broadcasting across local network peers.
    """
    def __init__(self):
        self.board = chess.Board()
        self.clients = []
        self.lock = threading.RLock()
        self.running = False
        self.sock = None
        self.server_only = True

        # role assignment: first client -> WHITE, second -> BLACK
        self.roles = {}

    def broadcast(self, msg: str):
        with self.lock:
            dead = []
            for c in self.clients:
                try:
                    c.sendall((msg + "\n").encode("utf-8"))
                except Exception:
                    dead.append(c)
            for c in dead:
                try:
                    self.clients.remove(c)
                except Exception:
                    pass


class LANController:
    """
    Multi-threaded LAN room controller (@author: Taha Siddiqui).
    
    Responsibilities & Networking Rules:
    - Host runs server in a daemon thread, remote clients join via TCP on port 5000.
    - Server validates chess moves, assigns player roles, and broadcasts FEN + LASTMOVE.
    - Queues thread-safe networking events to sync with the main Tkinter UI loop.
    """
    def __init__(self):
        self.server = None
        self.client = None
        self.client_thread = None
        self.server_thread = None

        self.events = queue.Queue()
        self.connected_count = 0

        self._stop = threading.Event()

    def get_host_ip(self) -> str:
        return get_local_ip()

    def stop(self):
        self._stop.set()
        self.connected_count = 0

        if self.client:
            try:
                self.client.close()
            except Exception:
                pass
        self.client = None

        if self.server and self.server.sock:
            try:
                self.server.sock.close()
            except Exception:
                pass
        self.server = None

    def poll(self):
        # no-op; connection count updated by threads
        pass

    # ---------- Host Modes ----------
    def start_host_server_only(self):
        self.stop()
        self._stop.clear()
        self.server = _LanServer()
        self.server_thread = threading.Thread(target=self._server_loop, daemon=True)
        self.server_thread.start()
        return self.server.board

    def start_host_plays_white(self):
        # same server; host also plays locally as white (role will be WHITE in app)
        self.stop()
        self._stop.clear()
        self.server = _LanServer()
        self.server.server_only = False
        self.server_thread = threading.Thread(target=self._server_loop, daemon=True)
        self.server_thread.start()
        return self.server.board

    # ---------- Join ----------
    def start_join(self, host_ip: str):
        self.stop()
        self._stop.clear()

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((host_ip, PORT))
        self.client = s
        self.client_thread = threading.Thread(target=self._client_loop, daemon=True)
        self.client_thread.start()

    def send_move(self, uci: str):
        if not self.client:
            return
        try:
            self.client.sendall((f"MOVE {uci}\n").encode("utf-8"))
        except Exception:
            self.events.put(("LAN_ERROR", "Failed to send move."))

    def send_resign(self):
        if not self.client:
            return
        try:
            self.client.sendall("RESIGN\n".encode("utf-8"))
        except Exception:
            self.events.put(("LAN_ERROR", "Failed to send resignation."))

    def send_draw_offer(self):
        if not self.client:
            return
        try:
            self.client.sendall("DRAWOFFER\n".encode("utf-8"))
        except Exception:
            self.events.put(("LAN_ERROR", "Failed to send draw offer."))

    def send_draw_response(self, accept: bool):
        if not self.client:
            return
        msg = "DRAWACCEPT\n" if accept else "DRAWDECLINE\n"
        try:
            self.client.sendall(msg.encode("utf-8"))
        except Exception:
            self.events.put(("LAN_ERROR", "Failed to send draw response."))

    def send_chat(self, sender: str, text: str):
        if self.client:
            try:
                self.client.sendall((f"CHAT {sender}: {text}\n").encode("utf-8"))
            except Exception:
                self.events.put(("LAN_ERROR", "Failed to send chat."))
        elif self.server:
            self.server.broadcast(f"CHAT {sender}: {text}")
            self.events.put(("LAN_CHAT", f"{sender}: {text}"))

    def send_emote(self, sender: str, emoji: str):
        if self.client:
            try:
                self.client.sendall((f"EMOTE {sender}|{emoji}\n").encode("utf-8"))
            except Exception:
                self.events.put(("LAN_ERROR", "Failed to send emote."))
        elif self.server:
            self.server.broadcast(f"EMOTE {sender}|{emoji}")
            self.events.put(("LAN_EMOTE", f"{sender}|{emoji}"))

    def broadcast_resign(self, role: str):
        if self.server:
            result = "0-1" if role == "WHITE" else "1-0"
            self.server.broadcast(f"END {result}")

    def broadcast_draw_offer(self, role: str):
        if self.server:
            self.server.broadcast(f"DRAWOFFER {role}")

    def broadcast_draw_accept(self):
        if self.server:
            self.server.broadcast("END 1/2-1/2")

    def broadcast_draw_decline(self, role: str):
        if self.server:
            self.server.broadcast(f"DRAWDECLINE {role}")

    # ---------- Server Thread ----------
    def _server_loop(self):
        self.server.running = True
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(("", PORT))
        sock.listen(2)
        self.server.sock = sock

        # accept up to 2 clients; keep listening
        while not self._stop.is_set():
            try:
                sock.settimeout(0.5)
                conn, _addr = sock.accept()
            except socket.timeout:
                continue
            except Exception:
                break

            with self.server.lock:
                max_clients = 2 if self.server.server_only else 1
                if len(self.server.clients) >= max_clients:
                    try:
                        conn.close()
                    except Exception:
                        pass
                    continue

                self.server.clients.append(conn)
                self.connected_count = len(self.server.clients)

                # assign role
                if self.server.server_only:
                    if "WHITE" not in self.server.roles.values():
                        self.server.roles[conn] = "WHITE"
                    else:
                        self.server.roles[conn] = "BLACK"
                else:
                    self.server.roles[conn] = "BLACK"

                # announce role to that client
                try:
                    conn.sendall((f"ROLE {self.server.roles[conn]}\n").encode("utf-8"))
                    conn.sendall((f"FEN {self.server.board.fen()}\n").encode("utf-8"))
                except Exception:
                    pass

                # notify host UI
                self.events.put(("LAN_INFO", f"Client connected ({self.connected_count}/{max_clients})."))

            t = threading.Thread(target=self._handle_client, args=(conn,), daemon=True)
            t.start()

    def _handle_client(self, conn):
        buff = b""
        while not self._stop.is_set():
            try:
                data = conn.recv(4096)
                if not data:
                    break
                buff += data
                while b"\n" in buff:
                    line, buff = buff.split(b"\n", 1)
                    msg = line.decode("utf-8", errors="ignore").strip()
                    self._handle_server_message(conn, msg)
            except Exception:
                break

        # disconnect
        try:
            conn.close()
        except Exception:
            pass
        if self.server:
            with self.server.lock:
                try:
                    self.server.clients.remove(conn)
                except Exception:
                    pass
                try:
                    del self.server.roles[conn]
                except Exception:
                    pass
                self.connected_count = len(self.server.clients)
                max_clients = 2 if self.server.server_only else 1
            self.events.put(("LAN_INFO", f"Client disconnected ({self.connected_count}/{max_clients})."))

    def _handle_server_message(self, conn, msg: str):
        if msg.startswith("MOVE "):
            uci = msg.split(" ", 1)[1].strip()
            with self.server.lock:
                role = self.server.roles.get(conn)
                if role == "WHITE" and self.server.board.turn != chess.WHITE:
                    return
                if role == "BLACK" and self.server.board.turn != chess.BLACK:
                    return

                try:
                    mv = chess.Move.from_uci(uci)
                except Exception:
                    return
                if mv not in self.server.board.legal_moves:
                    return

                self.server.board.push(mv)
                self.server.broadcast(f"LASTMOVE {uci}")
                self.server.broadcast(f"FEN {self.server.board.fen()}")

                required = 2 if self.server.server_only else 1
                if self.connected_count >= required:
                    self.server.broadcast("START 1")

                if self.server.board.is_game_over():
                    out = self.server.board.outcome()
                    if out:
                        self.server.broadcast(f"END {out.result()}")
            return

        if msg.startswith("CHAT "):
            payload = msg.split(" ", 1)[1].strip()
            with self.server.lock:
                self.server.broadcast(f"CHAT {payload}")
                self.events.put(("LAN_CHAT", payload))
            return

        if msg.startswith("EMOTE "):
            payload = msg.split(" ", 1)[1].strip()
            with self.server.lock:
                self.server.broadcast(f"EMOTE {payload}")
                self.events.put(("LAN_EMOTE", payload))
            return

        if msg == "RESIGN":
            with self.server.lock:
                role = self.server.roles.get(conn)
                result = "0-1" if role == "WHITE" else "1-0"
                self.server.broadcast(f"END {result}")
            return

        if msg == "DRAWOFFER":
            with self.server.lock:
                role = self.server.roles.get(conn)
                self.server.broadcast(f"DRAWOFFER {role}")
            return

        if msg == "DRAWACCEPT":
            with self.server.lock:
                self.server.broadcast("END 1/2-1/2")
            return

        if msg == "DRAWDECLINE":
            with self.server.lock:
                role = self.server.roles.get(conn)
                self.server.broadcast(f"DRAWDECLINE {role}")
            return

    # ---------- Client Thread ----------
    def _client_loop(self):
        self.connected_count = 1
        buff = b""
        while not self._stop.is_set():
            try:
                data = self.client.recv(4096)
                if not data:
                    break
                buff += data
                while b"\n" in buff:
                    line, buff = buff.split(b"\n", 1)
                    msg = line.decode("utf-8", errors="ignore").strip()
                    self._handle_client_message(msg)
            except Exception:
                break
        self.events.put(("LAN_ERROR", "Disconnected from host."))

    def _handle_client_message(self, msg: str):
        if msg.startswith("ROLE "):
            self.events.put(("LAN_ROLE", msg.split(" ", 1)[1].strip()))
            return
        if msg.startswith("FEN "):
            self.events.put(("LAN_FEN", msg.split(" ", 1)[1].strip()))
            return
        if msg.startswith("LASTMOVE "):
            self.events.put(("LAN_LASTMOVE", msg.split(" ", 1)[1].strip()))
            return
        if msg.startswith("START "):
            self.events.put(("LAN_START", "1"))
            return
        if msg.startswith("END "):
            self.events.put(("LAN_END", msg.split(" ", 1)[1].strip()))
            return
        if msg.startswith("DRAWOFFER "):
            self.events.put(("LAN_DRAWOFFER", msg.split(" ", 1)[1].strip()))
            return
        if msg.startswith("DRAWDECLINE "):
            self.events.put(("LAN_DRAWDECLINE", msg.split(" ", 1)[1].strip()))
            return
        if msg.startswith("CHAT "):
            self.events.put(("LAN_CHAT", msg.split(" ", 1)[1].strip()))
            return
        if msg.startswith("EMOTE "):
            self.events.put(("LAN_EMOTE", msg.split(" ", 1)[1].strip()))
            return
        self.events.put(("LAN_INFO", msg))
