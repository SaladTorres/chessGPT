import time
import board
import busio
import digitalio
from adafruit_mcp230xx.mcp23017 import MCP23017

def main():
    # 1. Start the I2C bus
    i2c = busio.I2C(board.SCL, board.SDA)

    # 2. Define our 5 board addresses
    # 0x23 (A2 soldered), 0x24 (A0,A1 soldered), 0x25 (A1), 0x26 (A0), 0x27 (None)
    addresses = [0x23, 0x24, 0x25, 0x26, 0x27]
    
    # Dictionary to hold the specific PA0 pins for each board
    pa0_pins = {}

    print("Connecting to 5 expanders...")
    for addr in addresses:
        try:
            mcp = MCP23017(i2c, address=addr)
            
            # Setup Pin 0 (PA0) for this specific board
            pin = mcp.get_pin(0)
            pin.direction = digitalio.Direction.INPUT
            pin.pull = digitalio.Pull.UP # Internally holds it at 3.3V safely
            
            # Store it in our dictionary with the address as the key
            pa0_pins[addr] = pin
            print(f"  - Successfully connected to board at {hex(addr)}")
        except ValueError:
            print(f"  ! Failed to find board at {hex(addr)}! Check wiring.")

    print("\n----------------------------------------------------")
    print("Monitoring PA0 on all 5 boards...")
    print("TOUCH PA0 TO GND TO TRIGGER (Do not use 5V!)")
    print("(Press Ctrl+C to quit)")
    print("----------------------------------------------------\n")

    # Keep track of previous states so we only print once when touched
    # True = OPEN (Not touched), False = CLOSED (Touched to Ground)
    previous_states = {addr: True for addr in pa0_pins.keys()}

    try:
        while True:
            # Check PA0 on every board, one by one
            for addr, pin in pa0_pins.items():
                
                # --- NEW SAFETY NET ADDED HERE ---
                try:
                    current_state = pin.value
                except OSError:
                    # If there is a split-second electrical glitch, skip this read
                    # and try again on the next loop instead of crashing!
                    continue 
                # ---------------------------------
                
                # If it is False now, but was True a millisecond ago...
                if current_state == False and previous_states[addr] == True:
                    print(f"Signal DETECTED on PA0 of expander: {hex(addr)}")
                
                # If it is True now, but was False a millisecond ago...
                elif current_state == True and previous_states[addr] == False:
                    print(f"Signal REMOVED on PA0 of expander: {hex(addr)}")
                
                # Update the history for the next loop
                previous_states[addr] = current_state
                
            time.sleep(0.05) # Scan very fast (50 milliseconds)

    except KeyboardInterrupt:
        print("\nTest stopped.")

if __name__ == "__main__":
    main()