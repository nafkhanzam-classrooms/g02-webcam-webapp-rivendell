from flask import Flask, send_from_directory, jsonify, request, Response
import cv2
import threading
import time

app = Flask(__name__)
camera_index = 0
cap = cv2.VideoCapture(camera_index)
lock = threading.Lock()

# Metrics
frames_served = 0
frame_times = []
metrics_lock = threading.Lock()

def get_fps():
    """Calculate average FPS from last 30 frames"""
    if len(frame_times) < 2:
        return 0.0
    time_diff = frame_times[-1] - frame_times[0]
    if time_diff <= 0:
        return 0.0
    return len(frame_times) / time_diff

@app.route('/')
def index():
    return send_from_directory('../client', 'index.html')

@app.route('/app.js')
def serve_js():
    return send_from_directory('../client', 'app.js')

@app.route('/camera', methods=['POST'])
def switch_camera():
    global camera_index, cap
    data = request.json
    new_idx = int(data.get('camera_index', 0))
    with lock:
        if new_idx != camera_index:
            camera_index = new_idx
            cap.release()
            cap = cv2.VideoCapture(camera_index)
    return jsonify({"status": "success", "camera_index": camera_index})

@app.route('/frame')
def get_frame():
    global frames_served, frame_times
    with lock:
        success, frame = cap.read()
    if not success:
        return "Failed to capture", 500
    
    # Kompresi sesuai konstrain (max 100,000 bytes)
    from utils import compress_frame
    buffer = compress_frame(frame)
    
    # Update metrics
    with metrics_lock:
        frames_served += 1
        frame_times.append(time.time())
        if len(frame_times) > 30:
            frame_times.pop(0)
    
    return Response(buffer, mimetype='image/jpeg')

@app.route('/stats')
def stats():
    """Return server statistics"""
    with metrics_lock:
        fps = get_fps()
        total_frames = frames_served
    return jsonify({
        "frames_served": total_frames,
        "fps": round(fps, 2),
        "active_camera": camera_index
    })

if __name__ == '__main__':
    app.run(port=8000, threaded=True)