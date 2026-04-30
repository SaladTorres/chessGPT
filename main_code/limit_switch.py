import RPi.GPIO as GPIO
import time

class ChessBotHardware:
    def __init__(self):
        # --- GPIO PIN CONFIGURATION ---
        self.PUL1, self.DIR1 = 18, 24
        self.PUL2, self.DIR2 = 17, 27
        self.LIMIT_X = 26 # X-axis Limit switch pin
        self.LIMIT_Y = 19 # Y-axis Limit switch pin (Change this to your actual pin)
        
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        
        # Setup motor pins
        GPIO.setup([self.PUL1, self.DIR1, self.PUL2, self.DIR2], GPIO.OUT)
        GPIO.output([self.PUL1, self.PUL2], GPIO.LOW)
        
        # Setup limit switches with internal Pull-Up resistors
        # Unpressed = HIGH, Pressed = LOW
        GPIO.setup([self.LIMIT_X, self.LIMIT_Y], GPIO.IN, pull_up_down=GPIO.PUD_UP)

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

    def calibrate_x(self, search_rpm=2500, backoff_rpm=200, homing_forward=True):
        """
        Moves the X axis until the X limit switch is hit, then slowly backs away.
        """
        steps_per_rev = 200
        
        # --- 1. FAST APPROACH ---
        # Set motor directions for the homing move (X uses SAME directions)
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

    def calibrate_y(self, search_rpm=2500, backoff_rpm=200, homing_forward=True):
        """
        Moves the Y axis until the Y limit switch is hit, then slowly backs away.
        """
        steps_per_rev = 200
        
        # --- 1. FAST APPROACH ---
        # Set motor directions for the homing move (Y uses OPPOSITE directions)
        dir1 = GPIO.HIGH if homing_forward else GPIO.LOW
        dir2 = GPIO.LOW if homing_forward else GPIO.HIGH
        GPIO.output(self.DIR1, dir1)
        GPIO.output(self.DIR2, dir2)
        
        search_delay = 1 / (((steps_per_rev * search_rpm) / 60) * 2)
        
        # Step continuously until switch is pressed (reads LOW)
        while GPIO.input(self.LIMIT_Y) == GPIO.HIGH:
            GPIO.output(self.PUL1, GPIO.HIGH)
            GPIO.output(self.PUL2, GPIO.HIGH)
            time.sleep(search_delay)
            GPIO.output(self.PUL1, GPIO.LOW)
            GPIO.output(self.PUL2, GPIO.LOW)
            time.sleep(search_delay)
            
        # --- 2. SLOW BACKOFF ---
        # Reverse the directions
        backoff_dir1 = GPIO.LOW if homing_forward else GPIO.HIGH
        backoff_dir2 = GPIO.HIGH if homing_forward else GPIO.LOW
        GPIO.output(self.DIR1, backoff_dir1)
        GPIO.output(self.DIR2, backoff_dir2)
        
        backoff_delay = 1 / (((steps_per_rev * backoff_rpm) / 60) * 2)
        
        # Step continuously until switch is released (reads HIGH)
        while GPIO.input(self.LIMIT_Y) == GPIO.LOW:
            GPIO.output(self.PUL1, GPIO.HIGH)
            GPIO.output(self.PUL2, GPIO.HIGH)
            time.sleep(backoff_delay)
            GPIO.output(self.PUL1, GPIO.LOW)
            GPIO.output(self.PUL2, GPIO.LOW)
            time.sleep(backoff_delay)
            
        print("calibrated at Y = 0")

    def cleanup(self):
        GPIO.cleanup()


# calibration coding
if __name__ == "__main__":
    bot = ChessBotHardware()
    
    try:
        print("Starting Full Homing Sequence...")
        print("Press Ctrl+C to abort.")
        
        # 1. Calibrate X Axis
        print("\nSearching for X limit switch...")
        bot.calibrate_x(search_rpm=1000, backoff_rpm=30, homing_forward=True)
        
        time.sleep(0.5) # Short pause between axes
        
        # 2. Calibrate Y Axis
        print("\nSearching for Y limit switch...")
        bot.calibrate_y(search_rpm=1000, backoff_rpm=30, homing_forward=False)
        
        print("\nAll axes calibrated successfully!")
        
    except KeyboardInterrupt:
        print("\nStopping operation and cleaning up...")
    finally:
        bot.cleanup()