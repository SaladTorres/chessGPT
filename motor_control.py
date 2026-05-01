import RPi.GPIO as GPIO
import time

class ChessBotHardware:
    def __init__(self):
        # --- GPIO PIN CONFIGURATION ---
        self.PUL1, self.DIR1 = 18, 24
        self.PUL2, self.DIR2 = 17, 27
        
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup([self.PUL1, self.DIR1, self.PUL2, self.DIR2], GPIO.OUT)
        GPIO.output([self.PUL1, self.PUL2], GPIO.LOW)

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

    def cleanup(self):
        GPIO.cleanup()

# --- Infinite Loop Execution ---
if __name__ == "__main__":
    bot = ChessBotHardware()
    
    # Configuration for the test
    TEST_STEPS = 1000  # Distance to move
    TEST_RPM = 600    # Speed
    
    try:
        print(f"Starting infinite oscillation at {TEST_RPM} RPM...")
        print("Press Ctrl+C to stop the motors.")
        
        while True:
            
            # Step A: Move X Forward
            bot.move_x(TEST_STEPS, rpm=TEST_RPM, forward=False)
            time.sleep(0.5) # Short pause to prevent mechanical stress
            bot.move_y(TEST_STEPS, rpm=TEST_RPM,forward=True)
            time.sleep(0.5)
            
            # Step B: Move X Backward
           # print("Moving X Backward...")
           # bot.move_x(TEST_STEPS, rpm=TEST_RPM, forward=False)
            # time.sleep(0.5)
            
            # Step C: Move Y Forward
          #  print("Moving Y Forward...")
         #   bot.move_y(TEST_STEPS, rpm=TEST_RPM, forward=True)
          #  time.sleep(0.5)
            
            # Step D: Move Y Backward
           # print("Moving Y Backward...")
            #bot.move_y(TEST_STEPS, rpm=TEST_RPM, forward=False)
           # time.sleep(0.5)
            
        #    bot.move_y(TEST_STEPS, rpm=TEST_RPM, forward=False)
         #   time.sleep(0.5)
          #  bot.move_x(TEST_STEPS, rpm=TEST_RPM, forward=True)
           # time.sleep(0.5)
    except KeyboardInterrupt:
        print("\nStopping oscillation and cleaning up...")
    finally:
        bot.cleanup()