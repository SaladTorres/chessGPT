import time
import board
import busio
import digitalio
from adafruit_mcp230xx.mcp23017 import MCP23017

def run_grid_scanner():
    i2c = busio.I2C(board.SCL, board.SDA)
    addresses = [0x23, 0x24, 0x25, 0x26, 0x27]
    all_pins = []

    print("Initializing 80 sensors across 5 boards...")
    
    for addr in addresses:
        try:
            mcp = MCP23017(i2c, address=addr)
            for i in range(16):
                p = mcp.get_pin(i)
                p.direction = digitalio.Direction.INPUT
                p.pull = digitalio.Pull.UP
                all_pins.append(p)
        except Exception as e:
            print(f"Error connecting to board {hex(addr)}: {e}")

    print("\n--- LIVE SENSOR GRID (1=PIECE, 0=EMPTY) ---")
    print("Columns are grouped by board (16 pins each)")
    
    try:
        while True:
            # Generate the string of 0s and 1s
            # We invert the value: if pin.value is False (grounded), we show 1
            results = []
            for pin in all_pins:
                results.append("1" if not pin.value else "0")
            
            # Group into blocks of 16 for easier reading
            display = " | ".join(["".join(results[i:i+16]) for i in range(0, 80, 16)])
            
            # Print to the same line
            print(f"\rBoard Order (23|24|25|26|27): {display}", end="", flush=True)
            
            time.sleep(0.05)
            
    except KeyboardInterrupt:
        print("\n\nScanning stopped.")

if __name__ == "__main__":
    run_grid_scanner()