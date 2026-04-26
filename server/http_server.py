from flask import Flask, send_from_directory, jsonify, request, Response
import cv2
import threading

app = Flask(__name__)
camera_index = 0
cap = cv2.VideoCapture(camera_index)
lock = threading.Lock()

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
    with lock:
        success, frame = cap.read()
    if not success:
        return "Failed to capture", 500
    
    # Kompresi sesuai konstrain (max 100,000 bytes)
    from utils import compress_frame
    buffer = compress_frame(frame)
    return Response(buffer, mimetype='image/jpeg')

if __name__ == '__main__':
    app.run(port=8000, threaded=True)