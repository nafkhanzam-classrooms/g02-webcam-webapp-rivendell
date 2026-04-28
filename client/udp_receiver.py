import socket
import struct
import cv2
import numpy as np
import time

UDP_IP = "0.0.0.0"
UDP_PORT = 5005
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))

frames_buffer = {}
packets_received = 0
frames_displayed = 0
last_stats_time = time.time()

while True:
    packet, addr = sock.recvfrom(1300)
    header = packet[:10]
    payload = packet[10:]
    
    packets_received += 1
    
    frame_id, chunk_id, total_chunks, payload_len = struct.unpack('!IHHH', header)
    
    if frame_id not in frames_buffer:
        frames_buffer[frame_id] = {}
    
    frames_buffer[frame_id][chunk_id] = payload
    
    if len(frames_buffer[frame_id]) == total_chunks:
        # Reassemble
        full_frame = b"".join([frames_buffer[frame_id][i] for i in range(total_chunks)])
        nparr = np.frombuffer(full_frame, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is not None:
            frames_displayed += 1
            cv2.imshow("UDP Stream", img)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        del frames_buffer[frame_id]
    
    # Print metrics every 1 second
    current_time = time.time()
    if current_time - last_stats_time >= 1.0:
        time_elapsed = current_time - last_stats_time
        pkt_rate = packets_received / time_elapsed
        frame_rate = frames_displayed / time_elapsed
        print(f"UDP Receiver - Packets/s: {pkt_rate:.1f} | Frames/s: {frame_rate:.1f} | Total: {packets_received} pkts, {frames_displayed} frames")
        packets_received = 0
        frames_displayed = 0
        last_stats_time = current_time