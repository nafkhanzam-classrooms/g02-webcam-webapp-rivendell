#!/usr/bin/env python3
"""
Mengambil frame dari http://127.0.0.1:8000/frame, membagi ke paket UDP
dengan format:
 [frame_id:4][chunk_id:2][total_chunks:2][payload_len:2][payload]
Header = 10 byte, Max packet 1200 byte.
"""

import socket, struct, requests, time, math

FRAME_URL   = "http://127.0.0.1:8001/frame"
DEST_IP     = "255.255.255.255"   # broadcast
DEST_PORT   = 5000
MTU         = 1200
HEADER_FMT  = "!IHHH"             # = 4 + 2 + 2 + 2  byte

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

last_frame_id = 0
while True:
    try:
        r = requests.get(FRAME_URL, timeout=0.5)
        if r.status_code != 200:  # belum ada frame
            time.sleep(0.1); continue
        frame = r.content
        frame_id = int(time.time()*1000) & 0xFFFFFFFF
        if frame_id == last_frame_id: continue
        last_frame_id = frame_id

        chunk_payload = MTU - struct.calcsize(HEADER_FMT)
        total_chunks  = math.ceil(len(frame)/chunk_payload)

        for chunk_id in range(total_chunks):
            start = chunk_id*chunk_payload
            payload = frame[start:start+chunk_payload]
            header  = struct.pack(HEADER_FMT, frame_id,
                                  chunk_id, total_chunks, len(payload))
            sock.sendto(header+payload, (DEST_IP, DEST_PORT))

        print(f"[UDP] Sent frame {frame_id} in {total_chunks} chunks")
        time.sleep(1/8)   # target 8 FPS
    except Exception as e:
        print("error:", e)
        time.sleep(0.2)