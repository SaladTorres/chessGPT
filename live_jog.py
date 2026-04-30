import sys
import tty
import termios
import time
import RPi.GPIO as GPIO

class Gantry:
    def __init__(self):
        self.PUL1, self.DIR1 = 18, 24  # X-Axis
        self.PUL2, self.DIR2 = 17, 27  # Y-Axis
        self.MM_PER_STEP = 0.05 
        
        self.current_x = 0.0
        self.current_y = 0.0
        
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup([self.PUL1, self.DIR1, self.PUL2, self.DIR2], GPIO.OUT)

    def execute_stepper_move(self, target_x, target_y):
        dx = target_x - self.current_x
        dy = target_y - self.current_y
        
        # Set Directions
        GPIO.output(self.DIR1, GPIO.HIGH if dx >= 0 else GPIO.LOW)
        GPIO.output(self.DIR2, GPIO.HIGH if dy >= 0 else GPIO.LOW)
        
        steps_x = int(abs(dx) / self.MM_PER_STEP)
        steps_y = int(abs(dy) / self.MM_PER_STEP)

        # To move both at once, we find which axis has more steps
        max_steps = max(steps_x, steps_y)
        
        # Timing: 0.001 is a good steady pace for most NEMA 17s
        pulse_delay = 0.001 

        for i in range(max_steps):
            # Pulse X if it still has steps left
            if i < steps_x:
                GPIO.output(self.PUL1, GPIO.HIGH)
            # Pulse Y if it still has steps left
            if i < steps_y:
                GPIO.output(self.PUL2, GPIO.HIGH)
            
            time.sleep(pulse_delay)
            
            GPIO.output(self.PUL1, GPIO.LOW)
            GPIO.output(self.PUL2, GPIO.LOW)
            
            time.sleep(pulse_delay)

        self.current_x = target_x
        self.current_y = target_y

def get_key():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        ch = sys.stdin.read(1)
        if ch == '\x1b':
            ch += sys.stdin.read(2)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch

def main():
    g = Gantry()
    step = 5.0 # mm
    print("STEADY JOG READY.")
    print("Use ARROWS. 'SPACE' to toggle 1mm/5mm. 'Q' to quit.")
    
    while True:
        key = get_key()
        tx, ty = g.current_x, g.current_y
        
        if key == '\x1b[A': ty += step   
        elif key == '\x1b[B': ty -= step 
        elif key == '\x1b[C': tx += step 
        elif key == '\x1b[D': tx -= step 
        elif key == ' ': 
            step = 5.0 if step == 1.0 else 1.0
            print(f"\rStep set to {step}mm    ", end="")
            continue
        elif key.lower() == 'q':
            print(f"\nFinal Position: X={g.current_x}, Y={g.current_y}")
            break
            
        g.execute_stepper_move(tx, ty)
        sys.stdout.write(f"\rCurrent Position: X={g.current_x:.2f}, Y={g.current_y:.2f}    ")
        sys.stdout.flush()

if __name__ == "__main__":
    main()