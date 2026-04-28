#!/usr/bin/env python3
"""
Menerima paket-paket UDP broadcast, merakit frame, lalu menampilkan
menggunakan OpenCV. Timeout 2 detik per frame.
"""

import socket
import struct
import time

import cv2
import numpy as np

PORT = 5000
HEADER_FMT = "!IHHH"
HEADER_LEN = struct.calcsize(HEADER_FMT)
TIMEOUT = 2.0

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("", PORT))
sock.settimeout(0.5)

frames = {}
stats_started_at = time.time()
stats_packets = 0
stats_frames = 0


def assemble(meta):
    return b"".join(meta["arrived"][i] for i in range(meta["total_chunks"]))


while True:
    try:
        pkt, _ = sock.recvfrom(1500)
        stats_packets += 1

        if len(pkt) < HEADER_LEN:
            continue

        frame_id, chunk_id, total_chunks, payload_len = struct.unpack(
            HEADER_FMT, pkt[:HEADER_LEN]
        )
        payload = pkt[HEADER_LEN:HEADER_LEN + payload_len]

        meta = frames.setdefault(
            frame_id,
            {"t0": time.time(), "total_chunks": total_chunks, "arrived": {}},
        )
        meta["arrived"][chunk_id] = payload

        if len(meta["arrived"]) == meta["total_chunks"]:
            jpeg = assemble(meta)
            img = cv2.imdecode(np.frombuffer(jpeg, np.uint8), cv2.IMREAD_COLOR)
            if img is not None:
                cv2.imshow("Mirrored Window", img)
                cv2.waitKey(1)
                stats_frames += 1
            frames.pop(frame_id, None)

        now = time.time()
        for fid in list(frames):
            if now - frames[fid]["t0"] > TIMEOUT:
                frames.pop(fid, None)

        if now - stats_started_at >= 1.0:
            elapsed = max(now - stats_started_at, 1e-6)
            print(
                f"[UDP receiver] packets/s={stats_packets / elapsed:.2f} "
                f"reconstructed frames/s={stats_frames / elapsed:.2f}"
            )
            stats_started_at = now
            stats_packets = 0
            stats_frames = 0
    except socket.timeout:
        now = time.time()
        for fid in list(frames):
            if now - frames[fid]["t0"] > TIMEOUT:
                frames.pop(fid, None)
        if now - stats_started_at >= 1.0:
            elapsed = max(now - stats_started_at, 1e-6)
            print(
                f"[UDP receiver] packets/s={stats_packets / elapsed:.2f} "
                f"reconstructed frames/s={stats_frames / elapsed:.2f}"
            )
            stats_started_at = now
            stats_packets = 0
            stats_frames = 0
    except KeyboardInterrupt:
        break

cv2.destroyAllWindows()
