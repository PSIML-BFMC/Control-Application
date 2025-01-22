import pygame
import time
import requests
import os

ENDPOINT = 'http://127.0.0.1:8000'

clear = lambda: os.system('cls')

# Initialize Pygame
pygame.init()
# Initialize the joystick
pygame.joystick.init()
# Check how many joysticks are connected
joystick_count = pygame.joystick.get_count()
if joystick_count == 0:
    print("No joysticks connected.")
else:
    print(f"{joystick_count} joystick(s) connected.")

# Initialize the first joystick
joystick = pygame.joystick.Joystick(0)
joystick.init()

print(f"Joystick name: {joystick.get_name()}")

steer_multiplier = 150
previous_angle = 0 # -steer_multiplier to steer-multiplier
previous_speed = 0 # 0 to 1
running_state = 0
# 1 - running
# 0 - idle
# -1 - brake idle
# -2 - brake brake

# Run a loop to read input from the joystick
try:
    while True:
        for event in pygame.event.get():
            if event.type == pygame.JOYAXISMOTION:
                steer_axis = joystick.get_axis(0)  # Usually the X axis for steering
                brake_pedal = joystick.get_axis(1)  # Adjust this if needed
                gas_pedal = joystick.get_axis(2)  # Adjust this if needed
                
                if previous_angle != int(steer_axis*steer_multiplier):
                    steer_body = {'angle': int(steer_axis*steer_multiplier)}
                    response = requests.post(ENDPOINT + '/steer', json=steer_body)
                    previous_angle = int(steer_axis*steer_multiplier)

                if brake_pedal < 0 and running_state != -2:
                    response = requests.post(ENDPOINT + '/brake')
                    running_state = -2
                    previous_speed = 0

                if brake_pedal < 0.95 and brake_pedal > 0 and running_state != -1:
                    response = requests.post(ENDPOINT + '/idle')
                    running_state = -1
                    previous_speed = 0

                if brake_pedal > 0.95 and running_state < 0:
                    running_state = 0
                    previous_speed = 0

                speed = (-gas_pedal+1)/2
                if gas_pedal < 0.95 and running_state >= 0 and abs(speed-previous_speed) > 0.03:
                    drive_body = {'speed': speed}
                    response = requests.post(ENDPOINT + '/drive', json=drive_body)
                    previous_speed = speed
                    running_state = 1
                
                if running_state != 0 and gas_pedal > 0.95 and brake_pedal > 0.95:
                    response = requests.post(ENDPOINT + '/idle')
                    running_state = 0
                    previous_speed = 0
                

                # print('Steering', steer_axis)
                # print('Gas:', gas_pedal)
                # print('Brake:', brake_pedal)

            if event.type == pygame.JOYBUTTONDOWN:
                button = event.button
                # print(f"Button {button} pressed.")

                if button == 5:
                    gear_body = {'gear': 'D'}
                    response = requests.post(ENDPOINT + '/set_gear', json=gear_body)
                
                elif button == 4:
                    gear_body = {'gear': 'R'}
                    response = requests.post(ENDPOINT + '/set_gear', json=gear_body)

            
        time.sleep(0.1)

except KeyboardInterrupt:
    print("Exiting...")

finally:
    pygame.joystick.quit()
    pygame.quit()
