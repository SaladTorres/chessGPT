import RPi.GPIO as GPIO
import time

class ChessBotHardware:
    def __init__(self):
        # --- GPIO PIN CONFIGURATION ---
        self.PUL1, self.DIR1 = 18, 24
        self.PUL2, self.DIR2 = 17, 27
        self.LIMIT_X = 26 # Limit switch pin
        
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        
        # Setup motor pins
        GPIO.setup([self.PUL1, self.DIR1, self.PUL2, self.DIR2], GPIO.OUT)
        GPIO.output([self.PUL1, self.PUL2], GPIO.LOW)
        
        # Setup limit switch with an internal Pull-Up resistor
        # Unpressed = HIGH, Pressed = LOW
        GPIO.setup(self.LIMIT_X, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    def _pulse_motors(self, motor1_dir, motor2_dir, steps, rpm):
        steps_per_rev = 200
        steps_per_second = (steps_per_rev * rpm) / 60
        delay = 1 / (steps_per_second * 2)
        
        GPIO.output(self.DIR1, motor1_dir)
        GPIO.output(self.DIR2, motor2_dir)
        
        for _ in range(steps):
            GPIO.output(self.PUL1, GPIO.HIGH)
            GPIO.output(self.PUL2, GPIO.HIGH)
            time.sleep(delay)
            GPIO.output(self.PUL1, GPIO.LOW)
            GPIO.output(self.PUL2, GPIO.LOW)
            time.sleep(delay)

    def move_x(self, steps, rpm=60, forward=True):
        direction = GPIO.HIGH if forward else GPIO.LOW
        self._pulse_motors(direction, direction, steps, rpm)

    def move_y(self, steps, rpm=60, forward=True):
        dir1 = GPIO.HIGH if forward else GPIO.LOW
        dir2 = GPIO.LOW if forward else GPIO.HIGH
        self._pulse_motors(dir1, dir2, steps, rpm)

    def calibrate_x(self, search_rpm=300, backoff_rpm=30, homing_forward=False):
        """
        Moves the X axis until the limit switch is hit, then slowly backs away.
        homing_forward=False assumes X=0 is in the backward/negative direction.
        """
        steps_per_rev = 200
        
        # --- 1. FAST APPROACH ---
        # Set motor directions for the homing move
        direction = GPIO.HIGH if homing_forward else GPIO.LOW
        GPIO.output(self.DIR1, direction)
        GPIO.output(self.DIR2, direction)
        
        search_delay = 1 / (((steps_per_rev * search_rpm) / 60) * 2)
        
        # Step continuously until switch is pressed (reads LOW)
        while GPIO.input(self.LIMIT_X) == GPIO.HIGH:
            GPIO.output(self.PUL1, GPIO.HIGH)
            GPIO.output(self.PUL2, GPIO.HIGH)
            time.sleep(search_delay)
            GPIO.output(self.PUL1, GPIO.LOW)
            GPIO.output(self.PUL2, GPIO.LOW)
            time.sleep(search_delay)
            
        # --- 2. SLOW BACKOFF ---
        # Reverse the direction
        backoff_direction = GPIO.LOW if homing_forward else GPIO.HIGH
        GPIO.output(self.DIR1, backoff_direction)
        GPIO.output(self.DIR2, backoff_direction)
        
        backoff_delay = 1 / (((steps_per_rev * backoff_rpm) / 60) * 2)
        
        # Step continuously until switch is released (reads HIGH)
        while GPIO.input(self.LIMIT_X) == GPIO.LOW:
            GPIO.output(self.PUL1, GPIO.HIGH)
            GPIO.output(self.PUL2, GPIO.HIGH)
            time.sleep(backoff_delay)
            GPIO.output(self.PUL1, GPIO.LOW)
            GPIO.output(self.PUL2, GPIO.LOW)
            time.sleep(backoff_delay)
            
        print("calibrated at X = 0")

    def cleanup(self):
        GPIO.cleanup()


# calibration coding
if __name__ == "__main__":
    bot = ChessBotHardware()
    
    try:
        print("Starting Homing Sequence...")
        print("Press Ctrl+C to abort.")
        
        # Run the X calibration
        bot.move_x(5000, 1000, False)
        bot.calibrate_x(search_rpm=300, backoff_rpm=30, homing_forward=True)
        
        # You can resume other movements here once calibrated
        # time.sleep(1)
        # bot.move_x(1000, rpm=600, forward=True)

    except KeyboardInterrupt:
        print("\nStopping operation and cleaning up...")
    finally:
        bot.cleanup()