import os
import json
from datetime import datetime, timedelta
from picamera2 import Picamera2
from picamera2.encoders import H264Encoder, MJPEGEncoder
from picamera2.outputs import FfmpegOutput, CircularOutput
import time
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

# Load configuration
with open('config.json', 'r') as f:
    config = json.load(f)

# Camera settings
resolution = tuple(config['resolution'])
frame_rate = config['frame_rate']
clip_duration = config['clip_duration']  # in seconds
output_dir = config['output_dir']
stream_port = config['stream_port']

# Ensure output directory exists
os.makedirs(output_dir, exist_ok=True)

# Initialize camera
picam2 = Picamera2()
video_config = picam2.create_video_configuration(main={"size": resolution}, lores={"size": (640, 480)})
picam2.configure(video_config)
picam2.set_controls({"FrameRate": frame_rate})

# Streaming setup using lores stream
stream_output = CircularOutput()
picam2.start_recording(MJPEGEncoder(), stream_output, name="lores")

# HTTP server for streaming
class StreamingHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/stream.mjpg':
            self.send_response(200)
            self.send_header('Content-type', 'multipart/x-mixed-replace; boundary=--jpgboundary')
            self.end_headers()
            while True:
                try:
                    frame = stream_output.get()
                    self.wfile.write(b'--jpgboundary\r\n')
                    self.send_header('Content-type', 'image/jpeg')
                    self.send_header('Content-length', str(len(frame)))
                    self.end_headers()
                    self.wfile.write(frame)
                    self.wfile.write(b'\r\n')
                except Exception as e:
                    break
        else:
            self.send_response(404)
            self.end_headers()

def start_streaming_server():
    server = HTTPServer(('', stream_port), StreamingHandler)
    server.serve_forever()

# Start streaming server in a separate thread
threading.Thread(target=start_streaming_server, daemon=True).start()

# Function to generate filename with timestamp
def generate_filename():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return os.path.join(output_dir, f"video_{timestamp}.mp4")

# Function to record a clip
def record_clip(duration):
    filename = generate_filename()
    encoder = H264Encoder()
    output = FfmpegOutput(filename)
    picam2.start_recording(encoder, output, name="main")
    time.sleep(duration)
    picam2.stop_recording(name="main")

# Function to manage storage
def manage_storage():
    while True:
        now = datetime.now()
        for filename in os.listdir(output_dir):
            if filename.endswith(".mp4"):
                file_path = os.path.join(output_dir, filename)
                # Extract timestamp from filename
                try:
                    timestamp_str = filename.split('_')[1].split('.')[0]
                    file_time = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                    if now - file_time > timedelta(days=1):
                        os.remove(file_path)
                except Exception as e:
                    print(f"Error processing {filename}: {e}")
        time.sleep(3600)  # Check every hour

# Start storage management in a separate thread
threading.Thread(target=manage_storage, daemon=True).start()

# Main recording loop
while True:
    record_clip(clip_duration)