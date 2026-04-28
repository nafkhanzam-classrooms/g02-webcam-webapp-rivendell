#!/usr/bin/env python3
"""
Mengambil frame dari http://127.0.0.1:8000/frame, membagi ke paket UDP
dengan format:
 [frame_id:4][chunk_id:2][total_chunks:2][payload_len:2][payload]
Header = 10 byte, Max packet 1200 byte.
"""

import math
import socket
import struct
import time
from hashlib import blake2b

import requests

FRAME_URL = "http://127.0.0.1:8000/frame"
DEST_IP = "255.255.255.255"
DEST_PORT = 5000
MTU = 1200
HEADER_FMT = "!IHHH"
HEADER_LEN = struct.calcsize(HEADER_FMT)
TARGET_FPS = 8

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)


def print_stats(sent_frames, sent_packets, sent_bytes, started_at):
    elapsed = max(time.time() - started_at, 1e-6)
    fps = sent_frames / elapsed
    throughput_kbps = (sent_bytes * 8 / 1000) / elapsed
    print(
        f"[UDP sender] fps={fps:.2f} packets/s={sent_packets / elapsed:.2f} "
        f"throughput={throughput_kbps:.2f} kbps"
    )


frame_counter = 0
last_digest = None
stats_started_at = time.time()
stats_frames = 0
stats_packets = 0
stats_bytes = 0
last_stats_print = time.time()

while True:
    loop_started_at = time.time()
    try:
        response = requests.get(FRAME_URL, timeout=0.5)
        if response.status_code != 200:
            time.sleep(0.1)
            continue

        frame = response.content
        digest = blake2b(frame, digest_size=8).digest()
        if digest == last_digest:
            time.sleep(max(0, (1 / TARGET_FPS) - (time.time() - loop_started_at)))
            continue
        last_digest = digest

        frame_counter = (frame_counter + 1) & 0xFFFFFFFF
        chunk_payload = MTU - HEADER_LEN
        total_chunks = math.ceil(len(frame) / chunk_payload)

        for chunk_id in range(total_chunks):
            start = chunk_id * chunk_payload
            payload = frame[start:start + chunk_payload]
            header = struct.pack(
                HEADER_FMT,
                frame_counter,
                chunk_id,
                total_chunks,
                len(payload),
            )
            packet = header + payload
            sock.sendto(packet, (DEST_IP, DEST_PORT))
            stats_packets += 1
            stats_bytes += len(packet)

        stats_frames += 1
        if time.time() - last_stats_print >= 1.0:
            print_stats(stats_frames, stats_packets, stats_bytes, stats_started_at)
            stats_started_at = time.time()
            stats_frames = 0
            stats_packets = 0
            stats_bytes = 0
            last_stats_print = stats_started_at

        time.sleep(max(0, (1 / TARGET_FPS) - (time.time() - loop_started_at)))
    except KeyboardInterrupt:
        break
    except Exception as exc:
        print(f"[UDP sender] error: {exc}")
        time.sleep(0.2)
