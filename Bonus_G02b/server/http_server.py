#!/usr/bin/env python3
"""
Raw-socket HTTP server untuk aplikasi mirroring.
Endpoint:
  GET  /              – Halaman guru (teacher dashboard)
  POST /upload-frame  – Upload JPEG dari browser (body=binary)
  GET  /frame         – Ambil frame JPEG terbaru (Content-Type: image/jpeg)
  GET  /stats         – Statistik JSON
"""

import io, socketserver, threading, time, json, socket, struct, math
# from http.server import BaseHTTPRequestHandler, HTTPServer
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORT            = 8001
MAX_FRAME_SIZE  = 100_000        # bytes
TARGET_FPS      = 8

# ---- UDP sender setup ----------------------------------------------------
DEST_IP      = "255.255.255.255"   # broadcast
DEST_PORT    = 5000
MTU          = 1200
HEADER_FMT   = "!IHHH"             # frame_id, chunk_id, total_chunks, payload_len
udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
# --------------------------------------------------------------------------

_state = {
    "latest_frame": b"",         # raw JPEG
    "frame_id":     0,
    "frames_uploaded": 0,
    "frames_served":   0,
    "upload_times":    [],       # timestamps for FPS window
}
_lock = threading.Lock()


def _fps(timestamps, window=5):
    """Hitung FPS dari timestamp dalam jendela `window` detik."""
    cutoff = time.time() - window
    timestamps[:] = [t for t in timestamps if t >= cutoff]
    return len(timestamps) / window if window else 0


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    # ---- helper -----------------------------------------------------------
    def _send(self, code:int, ctype:str="text/plain", body:bytes=b""):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if body:
            self.wfile.write(body)

    # ---- routes -----------------------------------------------------------
    def do_GET(self):
        if   self.path == "/":
            html = open("client/index.html","rb").read()
            return self._send(200, "text/html", html)

        elif self.path == "/frame":
            with _lock:
                data = _state["latest_frame"]
            if data:
                return self._send(200, "image/jpeg", data)
            return self._send(404, body=b"No frame")

        elif self.path == "/stats":
            with _lock:
                payload = json.dumps({
                    "frames_uploaded": _state["frames_uploaded"],
                    "frames_served":   _state["frames_served"],
                    "upload_fps":      round(_fps(_state["upload_times"]), 2),
                }).encode()
            return self._send(200, "application/json", payload)

        elif self.path == "/app.js":
            js = open("client/app.js", "rb").read()
            return self._send(200, "application/javascript", js)

        else:
            return self._send(404, body=b"Not Found")

    def do_POST(self):
        if self.path != "/upload-frame":
            return self._send(404, body=b"Not Found")

        length = int(self.headers.get("Content-Length","0"))
        if not 0 < length <= MAX_FRAME_SIZE:
            return self._send(413, body=b"Frame too large")

        data = self.rfile.read(length)
        with _lock:
            _state["latest_frame"]  = data
            _state["frame_id"]      += 1
            _state["frames_uploaded"] += 1
            _state["upload_times"].append(time.time())

        # ---- Send frame via UDP -------------------------------------------
        frame_id = _state["frame_id"]
        chunk_payload = MTU - struct.calcsize(HEADER_FMT)
        total_chunks  = math.ceil(len(data)/chunk_payload)

        for chunk_id in range(total_chunks):
            start = chunk_id*chunk_payload
            payload = data[start:start+chunk_payload]
            header  = struct.pack(HEADER_FMT, frame_id,
                                  chunk_id, total_chunks, len(payload))
            udp_sock.sendto(header+payload, (DEST_IP, DEST_PORT))
        # ------------------------------------------------------------------

        return self._send(200, body=b"OK")


if __name__ == "__main__":
    print(f"HTTP server listening on http://127.0.0.1:{PORT}")
    # HTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()