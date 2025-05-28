from picamera2 import Picamera2
from picamera2.encoders import H264Encoder
from picamera2.outputs import FfmpegOutput
import os
import time
from datetime import datetime

# Settings dictionary for easy customization
settings = {
    'resolution': (1920, 1080),  # 1080p resolution, compatible with Camera Module 3
    'framerate': 30,             # 30 fps, a usable preset for Camera Module 3
    'duration': 30,              # Duration of each clip in minutes
    'output_dir': '/home/pi/videos',  # Directory to store videos
    'retention_days': 1          # Keep videos for 1 day
}

# Supported settings for Camera Module 3:
# - 1920x1080 @ 30fps
# - 1280x720 @ 60fps
# - 640x480 @ 60fps
# Adjust 'resolution' and 'framerate' above as needed

# Ensure the output directory exists
if not os.path.exists(settings['output_dir']):
    os.makedirs(settings['output_dir'])

# Initialize and configure the camera
picam2 = Picamera2()
video_config = picam2.create_video_configuration(main={"size": settings['resolution']}, controls={"FrameRate": settings['framerate']})
picam2.configure(video_config)

def generate_filename():
    """Generate a filename with the current date and time."""
    now = datetime.now()
    return now.strftime("%Y%m%d_%H%M%S") + '.mp4'

def delete_old_files(directory, retention_days):
    """Delete MP4 files older than the retention period."""
    now = time.time()
    cutoff = now - (retention_days * 86400)  # Convert days to seconds
    for filename in os.listdir(directory):
        if filename.endswith('.mp4'):
            filepath = os.path.join(directory, filename)
            mtime = os.path.getmtime(filepath)
            if mtime < cutoff:
                os.remove(filepath)
                print(f"Deleted old file: {filename}")

# Main recording loop
while True:
    # Clean up old files
    delete_old_files(settings['output_dir'], settings['retention_days'])
    
    # Generate filename and full path
    filename = generate_filename()
    filepath = os.path.join(settings['output_dir'], filename)
    
    # Start recording
    print(f"Starting recording to {filepath}")
    encoder = H264Encoder()
    output = FfmpegOutput(filepath)
    picam2.start_recording(encoder, output)
    
    # Record for the specified duration
    time.sleep(settings['duration'] * 60)  # Convert minutes to seconds
    
    # Stop recording
    picam2.stop_recording()
    print(f"Finished recording to {filepath}")