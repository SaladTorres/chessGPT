import time
import RPi.GPIO as GPIO
from limit_switch import ChessBotHardware

class GantryControl:
    def __init__(self):
        self.hw = ChessBotHardware()
        
        # --- THEORETICAL BOARD CONSTANTS ---
        self.SQUARE_SIZE_MM = 45.0
        self.STEPS_PER_MM = 132.0     
        self.A1_OFFSET_X = 50.0     
        self.A1_OFFSET_Y = 50.0     
        
        self.curr_x_steps = 0
        self.curr_y_steps = 0

    def home_system(self):
        print("Homing... Stand back.")
        # Utilizing your good calibration code
        self.hw.calibrate_x(homing_forward=True)
        time.sleep(0.5)
        self.hw.calibrate_y(homing_forward=False)
        
        # Reset internal tracking to zero
        self.curr_x_steps = 0
        self.curr_y_steps = 0
        print("System ready at 0,0 (Home).")

    def move_to_square(self, square):
        """Translates 'e4' to steps and calls the motor execution."""
        row = ord(square[0].lower()) - ord('a') 
        col = int(square[1]) - 1                

        target_x_steps = int((self.A1_OFFSET_X + (col * self.SQUARE_SIZE_MM)) * self.STEPS_PER_MM)
        target_y_steps = int((self.A1_OFFSET_Y + (row * self.SQUARE_SIZE_MM)) * self.STEPS_PER_MM)

        diff_x = target_x_steps - self.curr_x_steps
        diff_y = target_y_steps - self.curr_y_steps

        # Call the helper function below
        self.execute_steps(diff_x, diff_y)
        
        self.curr_x_steps = target_x_steps
        self.curr_y_steps = target_y_steps
        print(f"Magnet arrived at {square}")

    def execute_steps(self, dx, dy, rpm=1500):
        """Moves X completely, then Y completely. Polarities flipped for free-space movement."""
        
        delay = 1 / (((200 * rpm) / 60) * 2)

        # --- 1. MOVE X AXIS FIRST ---
        if dx != 0:
            # FLIPPED: dir_x is now HIGH for positive moves. 
            # (If X was actually moving correctly before, change these back to LOW then HIGH)
            dir_x = GPIO.LOW if dx > 0 else GPIO.HIGH
            
            GPIO.output(self.hw.DIR1, dir_x)
            GPIO.output(self.hw.DIR2, dir_x)
            
            steps_x = abs(dx)
            for _ in range(steps_x):
                GPIO.output(self.hw.PUL1, GPIO.HIGH)
                GPIO.output(self.hw.PUL2, GPIO.HIGH)
                time.sleep(delay)
                GPIO.output(self.hw.PUL1, GPIO.LOW)
                GPIO.output(self.hw.PUL2, GPIO.LOW)
                time.sleep(delay)

        # --- 2. MOVE Y AXIS SECOND ---
        if dy != 0:
            # FLIPPED: This reverses the Y-axis so it drives AWAY from the limit switch
            dir_y1 = GPIO.HIGH if dy > 0 else GPIO.LOW
            dir_y2 = GPIO.LOW if dy > 0 else GPIO.HIGH
            
            GPIO.output(self.hw.DIR1, dir_y1)
            GPIO.output(self.hw.DIR2, dir_y2)
            
            steps_y = abs(dy)
            for _ in range(steps_y):
                GPIO.output(self.hw.PUL1, GPIO.HIGH)
                GPIO.output(self.hw.PUL2, GPIO.HIGH)
                time.sleep(delay)
                GPIO.output(self.hw.PUL1, GPIO.LOW)
                GPIO.output(self.hw.PUL2, GPIO.LOW)
                time.sleep(delay)

# --- MAIN EXECUTION BLOCK ---
if __name__ == "__main__":
    controller = GantryControl()
    try:
        controller.home_system()
        
        print("\n--- THEORETICAL CHESS BOARD ACTIVE ---")
        print("Enter a square (a1-h8) or 'q' to quit.")
        
        while True:
            cmd = input("\nTarget Square > ").strip().lower()
            
            if cmd == 'q':
                break
            
            if len(cmd) == 2 and 'a' <= cmd[0] <= 'h' and '1' <= cmd[1] <= '8':
                controller.move_to_square(cmd)
            else:
                print("Invalid Square! Try something like 'e4' or 'h8'.")

    except KeyboardInterrupt:
        print("\nEmergency Stop Triggered.")
    finally:
        GPIO.cleanup()