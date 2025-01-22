import socketio
import pygame
import time
import queue
import threading

sio = socketio.Client()

@sio.event
def connect():
    print("Connected to the server")

@sio.event
def disconnect():
    print("Disconnected from the server")


class SteeringWheelControl:
    def __init__(self, uri):
        self.uri = uri
        self.previous_angle = 0  # Steering angle range: -250 to 250
        self.previous_speed = 0  # Speed range: -500 to 500
        self.gear = "forward"  # Internal gear indicator: "forward" or "reverse"
        self.steer_multiplier = 250  # Multiplier for steering sensitivity
        self.message_queue = queue.Queue()  # Queue for outgoing messages
        self.brake_message_queue = ''
        self.speed_message_queue = ''
        self.steer_message_queue = ''
        self.stop_event = threading.Event()  # Event to stop worker threads
        self.previous_time = 0
        

        pygame.init()
        pygame.joystick.init()

        if pygame.joystick.get_count() == 0:
            print("No joysticks connected.")
            raise RuntimeError("No joysticks detected!")
        self.joystick = pygame.joystick.Joystick(0)
        self.joystick.init()
        print(f"Using joystick: {self.joystick.get_name()}")

    def send_message(self, name, value):
        # Format the message and add it to the queue
        message = '{"Name": "' + str(name) + '", "Value": "' + str(value) + '"}'
        if name == 'Brake':
            self.brake_message_queue = message
        elif name == 'SpeedMotor':
            self.speed_message_queue = message
        elif name == 'SteerMotor':
            self.steer_message_queue = message

        # self.message_queue.put(message)

    def worker_thread(self):
        # Send messages from the queue at a controlled interval
        while not self.stop_event.is_set():
            try:
                if self.brake_message_queue:
                    time.sleep(0.05)
                    sio.emit("message", self.brake_message_queue)
                    print(f"Sent: {self.brake_message_queue}")
                    self.brake_message_queue = ''
                
                elif self.speed_message_queue:
                    sio.emit("message", self.speed_message_queue)
                    print(f"Sent: {self.speed_message_queue}")
                    self.speed_message_queue = ''

                elif self.steer_message_queue:
                    sio.emit("message", self.steer_message_queue)
                    print(f"Sent: {self.steer_message_queue}")
                    self.steer_message_queue = ''

                # if not self.message_queue.empty():
                #     message = self.message_queue.get()
                #     sio.emit("message", message)
                #     print(f"Sent: {message}")
                #     self.message_queue.task_done()
            except Exception as e:
                print(f"Error sending message: {e}")
            time.sleep(0.06)  # Throttle message sending to 20 Hz (50 ms interval)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.JOYBUTTONDOWN:
                button = event.button
                # Update internal gear indicator
                if button == 5:  # Right bumper for forward
                    self.gear = "forward"
                    print("Gear set to forward")
                elif button == 4:  # Left bumper for reverse
                    self.gear = "reverse"
                    print("Gear set to reverse")
            
    def poll_inputs(self):
        while not self.stop_event.is_set():
            time.sleep(0.1)  # Poll every 100 ms

            # Read joystick inputs
            steer_axis = self.joystick.get_axis(0)  # Steering axis (usually X)
            brake_pedal = self.joystick.get_axis(1)  # Brake pedal axis (1 to -1)
            gas_pedal = self.joystick.get_axis(2)  # Gas pedal axis (1 to -1)

            # Handle steering
            steer_angle = int(steer_axis * self.steer_multiplier)
            if abs(steer_angle - self.previous_angle) > 25:  # Only send significant changes
                self.send_message("SteerMotor", steer_angle)
                self.previous_angle = steer_angle

            # Handle braking
            if brake_pedal < 0.95:  # Brake pressed
                self.send_message("Brake", self.previous_angle)
                self.previous_speed = 0
                running = False
                continue

            # Handle acceleration
            if gas_pedal > 0.95 and abs(self.previous_speed) > 0:
                self.send_message("SpeedMotor", 0)
                self.previous_speed = 0
            elif gas_pedal < 0.95 and brake_pedal > 0.95:  # Gas pedal pressed
                normalized_speed = int((1 - gas_pedal)/2 * 500)  # Normalize to 0-500
                if self.gear == "reverse":
                    normalized_speed = -normalized_speed  # Reverse direction
                if abs(normalized_speed - self.previous_speed) > 50:  # Avoid redundant messages
                    self.send_message("SpeedMotor", normalized_speed)
                    running = True
                    self.previous_speed = normalized_speed



    def start(self):
        sio.connect(self.uri)
        print("Steering wheel control activated")

        # Start the worker thread for sending messages
        threading.Thread(target=self.worker_thread, daemon=True).start()

        threading.Thread(target=self.poll_inputs, daemon=True).start()


        try:
            while not self.stop_event.is_set():
                self.handle_events()
        except KeyboardInterrupt:
            print("Exiting steering wheel control...")
        finally:
            self.stop()

    def stop(self):
        self.stop_event.set()
        sio.disconnect()
        pygame.quit()
