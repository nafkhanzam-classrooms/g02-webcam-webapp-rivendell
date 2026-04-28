#!/usr/bin/env python3
"""
Menerima paket-paket UDP broadcast, merakit frame, lalu menampilkan
menggunakan OpenCV.  Timeout 2 detik per frame.
"""

import socket, struct, time, cv2
import numpy as np

PORT        = 5000
HEADER_FMT  = "!IHHH"
HEADER_LEN  = struct.calcsize(HEADER_FMT)
TIMEOUT     = 2.0   # detik untuk membuang frame lama

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("", PORT))
sock.settimeout(0.5)

frames = {}   # frame_id -> {t0, total_chunks, arrived:{id:bytes}}

def assemble(frame_id, meta):
    data = b''.join(meta["arrived"][i] for i in range(meta["total_chunks"]))
    return data

while True:
    try:
        pkt, _ = sock.recvfrom(1500)
        hdr = struct.unpack(HEADER_FMT, pkt[:HEADER_LEN])
        frame_id, chunk_id, total_chunks, plen = hdr
        payload = pkt[HEADER_LEN:HEADER_LEN+plen]

        meta = frames.setdefault(frame_id,
                 {"t0": time.time(), "total_chunks": total_chunks, "arrived":{}})
        meta["arrived"][chunk_id] = payload

        # lengkap?
        if len(meta["arrived"]) == meta["total_chunks"]:
            jpeg = assemble(frame_id, meta)
            img  = cv2.imdecode(np.frombuffer(jpeg, np.uint8), cv2.IMREAD_COLOR)
            if img is not None:
                cv2.imshow("Mirrored Window", img)
                cv2.waitKey(1)
            frames.pop(frame_id, None)

        # buang frame kadaluarsa
        now=time.time()
        for fid in list(frames):
            if now-frames[fid]["t0"] > TIMEOUT:
                frames.pop(fid, None)
    except socket.timeout:
        continue
    except KeyboardInterrupt:
        break