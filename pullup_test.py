import time
import board
import busio
import digitalio
from adafruit_mcp230xx.mcp23017 import MCP23017

def main():
    i2c = busio.I2C(board.SCL, board.SDA)
    
    print("Connecting to Board 0x27...")
    try:
        mcp = MCP23017(i2c, address=0x27)
    except Exception as e:
        print(f"Failed to connect: {e}")
        return

    print("Configuring 16 pins and turning on Pull-Ups...")
    pins = []
    for i in range(16):
        pin = mcp.get_pin(i)
        pin.direction = digitalio.Direction.INPUT
        pin.pull = digitalio.Pull.UP
        pins.append(pin)

    print("\nReading pins... (Everything disconnected should read TRUE)")
    print("-" * 50)
    
    try:
        while True:
            failed_pins = []
            for i in range(16):
                # If a pin is False, the pull-up failed or data scrambled!
                if pins[i].value == False:
                    failed_pins.append(i)
            
            if failed_pins:
                print(f"[!] GHOST INPUT DETECTED on pins: {failed_pins}")
            else:
                print("[-] All 16 pins are perfectly stable (TRUE).")
                
            time.sleep(0.5)
            
    except KeyboardInterrupt:
        print("\nTest stopped.")

if __name__ == "__main__":
    main()