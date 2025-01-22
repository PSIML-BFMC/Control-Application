from flask_socketio import SocketIO, emit
from flask_cors import CORS
import base64
import time
import cv2
from flask import Flask
import os

# Create Flask app and Socket.IO server
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")
CORS(app, supports_credentials=True)

# Load the image once at the start
script_dir = os.path.dirname(os.path.abspath(__file__))

# Join the script directory with the image file name
image_path = os.path.join(script_dir, "test7.jpg")
image = cv2.imread(image_path)
if image is None:
    raise ValueError(f"Image not found at {image_path}")

# Function to encode the image as Base64
def encode_image(image):
    _, buffer = cv2.imencode(".jpg", image)
    return base64.b64encode(buffer).decode("utf-8")

# Asynchronous function to send camera data periodically
def send_camera_data():
    try:
        encoded_image = encode_image(image)
        while True:
            # Send image data as an event
            socketio.emit("serialCamera", {"value": encoded_image})
            socketio.sleep(0.1)  # Send data every 100 ms
    except Exception as e:
        print(f"Error: {e}")

# Event to handle client connections
@socketio.on("connect")
def handle_connect():
    print("Client connected")
    # Start sending data to the newly connected client
    socketio.start_background_task(send_camera_data)

# Event to handle client disconnections
@socketio.on("disconnect")
def handle_disconnect():
    print("Client disconnected")

# Event to receive messages from clients
@socketio.on("message")
def handle_message(data):
    print(f"Received message: {data}")

# Main function
if __name__ == "__main__":
    # Run the Flask app with Socket.IO
    socketio.run(app, host="127.0.0.1", port=5005)
