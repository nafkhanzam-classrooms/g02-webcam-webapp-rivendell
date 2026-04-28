import socket
import requests
import struct
import time
from utils import chunk_data

UDP_IP = "127.0.0.1"
UDP_PORT = 5005
HTTP_URL = "http://127.0.0.1:8000/frame"
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

frame_id = 0
packets_sent = 0
total_bytes_sent = 0
last_stats_time = time.time()

while True:
    try:
        response = requests.get(HTTP_URL, timeout=2)
        if response.status_code == 200:
            data = response.content
            chunks = list(chunk_data(data))
            total_chunks = len(chunks)
            
            for i, chunk in enumerate(chunks):
                header = struct.pack('!IHHH', frame_id, i, total_chunks, len(chunk))
                packet = header + chunk
                sock.sendto(packet, (UDP_IP, UDP_PORT))
                packets_sent += 1
                total_bytes_sent += len(packet)
            
            frame_id = (frame_id + 1) % 4294967295
            
            # Print metrics every 1 second
            current_time = time.time()
            if current_time - last_stats_time >= 1.0:
                fps = 1.0 / max(1/8, current_time - last_stats_time)  # ~8 FPS target
                throughput_kbps = (total_bytes_sent * 8) / 1000 / (current_time - last_stats_time)
                print(f"UDP Sender - FPS: {fps:.1f} | Throughput: {throughput_kbps:.1f} kbps | Packets: {packets_sent}")
                packets_sent = 0
                total_bytes_sent = 0
                last_stats_time = current_time
            
            time.sleep(1/8) # Target 8 FPS
    except Exception as e:
        print(f"Error: {e}")