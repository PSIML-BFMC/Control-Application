import socketio
import base64
import cv2
import numpy as np
from threading import Thread
import time
from threads_lanes import *

sio = socketio.Client()

@sio.event
def connect():
    print("Connected to the server")

@sio.event
def disconnect():
    print("Disconnected from the server")

class CameraHandler:
    def __init__(self, uri):
        self.uri = uri
        self.running = True
        self.frame = None
        self.last_display_time = 0
        self.display_interval = 0.14  # Limit display updates to 20 FPS (50 ms)

    def on_camera_data(self, data):
        try:
            encoded_image = data.get("value")
            if encoded_image:
                image_data = base64.b64decode(encoded_image)
                np_array = np.frombuffer(image_data, np.uint8)
                self.frame = cv2.imdecode(np_array, cv2.IMREAD_COLOR)
                lane_image=np.copy(self.frame)
                height,width,_=lane_image.shape
                lines=detect_lines(lane_image)
                average_lines=average_slope_intersect(height,lines)
                line_image=display_lines(lane_image,average_lines)
                combo_image=cv2.addWeighted(lane_image,0.8,line_image,1,1)
                st_angle=get_steering_angle(height,width,average_lines)
                self.frame=display_heading_line(combo_image,st_angle)

        except Exception as e:
            print(f"Error processing camera data: {e}")

    def start(self):
        sio.connect(self.uri)
        sio.on("serialCamera", self.on_camera_data)
        print("Camera handler activated")

        try:
            while self.running:
                if self.frame is not None:
                    current_time = time.time()
                    if current_time - self.last_display_time >= self.display_interval:
                        cv2.imshow("Car Camera", self.frame)
                        self.last_display_time = current_time

                    # Handle OpenCV window interactions
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        self.running = False
                        break
        except KeyboardInterrupt:
            print("Exiting camera handler...")
        finally:
            self.stop()

    def stop(self):
        self.running = False
        cv2.destroyAllWindows()
        sio.disconnect()
