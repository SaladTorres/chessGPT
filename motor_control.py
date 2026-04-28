import RPi.GPIO as GPIO
import time

PUL = 18
DIR = 24

GPIO.setmode(GPIO.BCM)
GPIO.setup(PUL, GPIO.OUT)
GPIO.setup(DIR, GPIO.OUT)

def move_with_velocity(steps, direction, rpm):
    # Convert RPM to a pulse delay
    # Formula: 1 / (((Steps_Per_Rev * RPM) / 60) * 2)
    steps_per_rev = 200 # Standard for NEMA 17 at Full Step
    steps_per_second = (steps_per_rev * rpm) / 60
    delay = 1 / (steps_per_second * 2)
    
    GPIO.output(DIR, direction)
    
    for _ in range(steps):
        GPIO.output(PUL, GPIO.HIGH)
        time.sleep(delay)
        GPIO.output(PUL, GPIO.LOW)
        time.sleep(delay)

try:
    # Adjust these variables to control your bot's "feel"
    target_steps = 3000  # 180 degrees (π radians)
    speed_rpm = 300      # 1 rotation per second
    
    print(f"Oscillating at {speed_rpm} RPM. Press Ctrl+C to stop.")
    
    while True:
        # Move to PI (180 degrees)
        move_with_velocity(target_steps, 1, speed_rpm)
        time.sleep(0.5) # Pause to let the chess piece settle
        
        # Move back to 0
        move_with_velocity(target_steps, 0, speed_rpm)
        time.sleep(0.5)

except KeyboardInterrupt:
    print("\nStopping motor safely...")
finally:
    GPIO.cleanup()
