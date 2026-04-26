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

while True:
    try:
        response = requests.get(HTTP_URL, timeout=2)
        if response.status_code == 200:
            data = response.content
            chunks = list(chunk_data(data))
            total_chunks = len(chunks)
            
            for i, chunk in enumerate(chunks):
                header = struct.pack('!IHHH', frame_id, i, total_chunks, len(chunk))
                sock.sendto(header + chunk, (UDP_IP, UDP_PORT))
            
            frame_id = (frame_id + 1) % 4294967295
            time.sleep(1/8) # Target 8 FPS
    except Exception as e:
        print(f"Error: {e}")