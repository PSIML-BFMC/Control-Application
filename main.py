import socketio
from threading import Thread
from keyboard_control import KeyboardControl
from steering_wheel_control import SteeringWheelControl
from camera_handler import CameraHandler


CAR_URI = "http://192.168.43.39:5005"
LOCAL_URI = "http://127.0.0.1:5005"
SERVER_URI = LOCAL_URI


sio = socketio.Client()

@sio.event
def connect():
    print("Connected to the server")
    message = '{"Name": "Klem", "Value": "30"}'
    sio.emit("message", message)
    print("Initialization message sent")

@sio.event
def disconnect():
    print("Disconnected from the server")

def run_keyboard_control():
    keyboard_control = KeyboardControl(SERVER_URI)
    keyboard_control.start()

def run_steering_wheel_control():
    steering_wheel_control = SteeringWheelControl(SERVER_URI)
    steering_wheel_control.start()

def run_camera_handler():
    camera_handler = CameraHandler(SERVER_URI)
    camera_handler.start()


def main():
    try:
        print("Starting the car control demo...")
        sio.connect(SERVER_URI)

        mode = input("Select control mode (keyboard/steering): ").strip().lower()
        if mode == "keyboard":
            Thread(target=run_keyboard_control).start()
        elif mode == "steering":
            Thread(target=run_steering_wheel_control).start()
        else:
            print("Invalid mode selected")
        
        Thread(target=run_camera_handler).start()

    except KeyboardInterrupt:
        print("bye bye")
    finally:
        sio.disconnect()

if __name__ == "__main__":
    main()
