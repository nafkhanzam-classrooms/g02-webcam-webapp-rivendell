import cv2

def compress_frame(frame, quality=50):
    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
    _, buffer = cv2.imencode('.jpg', frame, encode_param)
    return buffer.tobytes()

def chunk_data(data, chunk_size=1190):
    for i in range(0, len(data), chunk_size):
        yield data[i:i + chunk_size]