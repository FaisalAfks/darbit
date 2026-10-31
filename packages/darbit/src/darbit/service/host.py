"""The service's socket: clients connect on 127.0.0.1, say hello with the token, then send requests.

The port and token are in an address file in darbit's data folder, readable only by the user, so only their own
programs connect. One service per user: a second `darbit serve` sees the first answering and leaves. Each request
runs on its own thread (stopping a bot can take seconds); every event on darbit's bus goes to every client.
"""

import hmac
import json
import os
import secrets
import socketserver
import threading
from pathlib import Path

from .. import events, paths
from . import methods
from .protocol import HOST, VERSION, Event, Hello, ProtocolError, Reply, Request, decode, encode

ADDRESS = "service.json"


def address_file() -> Path:
    return paths.data_dir() / ADDRESS


class Service:
    """darbit's service on a free port (or `port`), until shutdown()."""

    def __init__(self, port: int = 0) -> None:
        self.token = secrets.token_urlsafe(24)
        self.server = _Server((HOST, port), _Connection)
        self.server.service = self
        self.connections: set[_Connection] = set()
        self.lock = threading.Lock()
        self.stop_listening = events.listen(self.broadcast)

    @property
    def port(self) -> int:
        return self.server.server_address[1]

    def serve_forever(self) -> None:
        """Write the address file and answer clients until shutdown()."""
        _write_address(self.port, self.token)
        try:
            self.server.serve_forever(poll_interval=0.2)
        finally:
            self.stop_listening()
            self.server.server_close()
            _remove_address(self.port)

    def shutdown(self) -> None:
        threading.Thread(target=self.server.shutdown, name="darbit-service-stop", daemon=True).start()

    def broadcast(self, topic: str, data: dict) -> None:
        with self.lock:
            connections = list(self.connections)
        for connection in connections:
            connection.send(Event(topic, data))

    def answer(self, request: Request) -> Reply:
        if request.method == "service.ping":
            return Reply(request.id, {"version": VERSION, "pid": os.getpid(), "methods": sorted(methods.METHODS)})
        if request.method == "service.stop":
            self.shutdown()
            return Reply(request.id, {"stopping": True})
        try:
            return Reply(request.id, methods.call(request.method, request.params))
        except (ValueError, KeyError, OSError) as error:
            return Reply(request.id, error=str(error) or type(error).__name__)


class _Server(socketserver.ThreadingTCPServer):
    daemon_threads = True
    allow_reuse_address = True
    service: Service


class _Connection(socketserver.StreamRequestHandler):
    """One client: hello first, then requests, each answered on its own thread."""

    server: _Server

    def setup(self) -> None:
        super().setup()
        self.send_lock = threading.Lock()

    def handle(self) -> None:
        service = self.server.service
        if not self._greeted(service):
            return
        with service.lock:
            service.connections.add(self)
        try:
            for line in self.rfile:
                try:
                    message = decode(line)
                except ProtocolError as error:
                    self.send(Reply(0, error=str(error)))
                    continue
                if isinstance(message, Request):
                    threading.Thread(target=self._answer, args=(message,), daemon=True).start()
        finally:
            with service.lock:
                service.connections.discard(self)

    def _greeted(self, service: Service) -> bool:
        try:
            hello = decode(self.rfile.readline())
        except ProtocolError:
            return False
        if not isinstance(hello, Hello) or not hmac.compare_digest(str(hello.token), service.token):
            self.send(Reply(0, error="wrong token: read it from the service's address file"))
            return False
        self.send(Reply(0, {"version": VERSION}))
        return True

    def _answer(self, request: Request) -> None:
        self.send(self.server.service.answer(request))

    def send(self, message: Reply | Event) -> None:
        try:
            with self.send_lock:
                self.wfile.write(encode(message))
                self.wfile.flush()
        except OSError:
            pass  # the client left; handle() ends when its socket closes


def _write_address(port: int, token: str) -> None:
    path = address_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps({"port": port, "token": token, "pid": os.getpid()}), encoding="utf-8")
    if os.name == "posix":
        temporary.chmod(0o600)
    temporary.replace(path)


def _remove_address(port: int) -> None:
    """Remove the address file, if it's still this service's."""
    path = address_file()
    try:
        if json.loads(path.read_text(encoding="utf-8")).get("port") == port:
            path.unlink()
    except (OSError, ValueError):
        pass
