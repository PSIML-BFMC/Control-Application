import socketio
from pynput import keyboard

sio = socketio.Client()

@sio.event
def connect():
    print("Connected to the server")

@sio.event
def disconnect():
    print("Disconnected from the server")

class KeyboardControl:
    def __init__(self, uri):
        self.uri = uri
        self.speed = 0
        self.direction = 0

    def send_message(self, name, value):
        message = '{"Name": "' + str(name) + '", "Value": "' + str(value) + '"}'
        sio.emit("message", message)  # Replace "message" with the correct event name
        print(f"Sent: {message}")

    def on_press(self, key):
        try:
            if key.char == 'w':
                self.speed = min(500, self.speed + 50)
                self.send_message("SpeedMotor", self.speed)
            elif key.char == 's':
                self.speed = max(-500, self.speed - 50)
                self.send_message("SpeedMotor", self.speed)
            elif key.char == 'a' and self.direction != -250:
                self.direction = -250  # Left turn
                self.send_message("SteerMotor", self.direction)
            elif key.char == 'd' and self.direction != 250:
                self.direction = 250  # Right turn
                self.send_message("SteerMotor", self.direction)
            elif key.char == 'c':
                self.speed = 0
                self.send_message("Brake", self.direction)
            elif key.char == 'q':
                exit()
        except Exception as e:
            print("oh no, some error I don't care about")

    def on_release(self, key):
        try:
            if key.char in ['a', 'd']:
                self.direction = 0  # Reset to center when key is released
                self.send_message("SteerMotor", self.direction)
        except AttributeError:
            pass

    def start(self):
        sio.connect(self.uri)
        print("Keyboard control activated")
        with keyboard.Listener(on_press=self.on_press, on_release=self.on_release) as listener:
            listener.join()
