import time
import board
import busio
import digitalio
from adafruit_mcp230xx.mcp23017 import MCP23017

def get_current_board_state(all_pins):
    """
    Reads all 80 pins and returns a dictionary of their states.
    If an I2C glitch occurs during reading, returns None.
    """
    state = {}
    for addr, pin_list in all_pins.items():
        state[addr] = []
        for pin in pin_list:
            try:
                state[addr].append(pin.value)
            except OSError:
                return None 
    return state


def main():
    # 1. Start the I2C bus
    i2c = busio.I2C(board.SCL, board.SDA)

    # 2. Define our 5 board addresses
    addresses = [0x23, 0x24, 0x25, 0x26, 0x27]
    all_pins = {}

    print("Initializing boards and mapping 80 pins...")
    
    for addr in addresses:
        try:
            mcp = MCP23017(i2c, address=addr)
            all_pins[addr] = []
            
            # Setup all 16 pins with a RETRY LOOP for safety
            for pin_num in range(16):
                pin = mcp.get_pin(pin_num)
                
                # --- NEW RETRY LOGIC FOR SETUP ---
                configured = False
                for attempt in range(5):
                    try:
                        pin.direction = digitalio.Direction.INPUT
                        pin.pull = digitalio.Pull.UP 
                        configured = True
                        break # Success! Break out of the retry loop.
                    except OSError:
                        # If a wire glitch happens, wait 50ms and try again
                        time.sleep(0.05)
                
                if not configured:
                    print(f"  ! Warning: Repeatedly failed to configure Pin {pin_num} on {hex(addr)}")
                # ---------------------------------
                
                all_pins[addr].append(pin)
                
            print(f"  - Board {hex(addr)} initialized (16 pins ready)")
        except ValueError:
            print(f"  ! Failed to find board at {hex(addr)}! Check wiring.")
        except OSError:
            print(f"  ! I2C Communication dropped while talking to {hex(addr)}.")

    # Get the initial baseline state before we start the loop
    baseline_state = get_current_board_state(all_pins)
    while baseline_state is None:
        time.sleep(0.05)
        baseline_state = get_current_board_state(all_pins)

    print("\n----------------------------------------------------")
    print("Board logic ready! Waiting for movement...")
    print("(Press Ctrl+C to quit)")
    print("----------------------------------------------------\n")

    is_settling = False
    pending_state = None
    settling_start_time = 0

    try:
        while True:
            current_state = get_current_board_state(all_pins)
            
            if current_state is None:
                continue 

            if current_state == baseline_state:
                if is_settling:
                    print("[-] Board returned to previous state. Move cancelled.")
                    is_settling = False
                    
            else:
                if not is_settling or current_state != pending_state:
                    print("[!] Board state changed. Waiting 3 seconds for settling...")
                    pending_state = current_state
                    settling_start_time = time.time()
                    is_settling = True
                
                elif current_state == pending_state:
                    if time.time() - settling_start_time >= 3.0:
                        print("\n================ MOVE CONFIRMED ================")
                        
                        pieces_removed = []
                        pieces_placed = []

                        for addr in baseline_state:
                            for i in range(16):
                                old_val = baseline_state[addr][i]
                                new_val = current_state[addr][i]
                                
                                if old_val != new_val:
                                    if new_val == False:
                                        pieces_placed.append(f"Expander {hex(addr)} | Pin {i}")
                                    else:
                                        pieces_removed.append(f"Expander {hex(addr)} | Pin {i}")

                        if pieces_removed:
                            print("Pieces Picked Up (OPENED):")
                            for move in pieces_removed:
                                print(f"  [-] {move}")
                        
                        if pieces_placed:
                            print("Pieces Set Down (CLOSED):")
                            for move in pieces_placed:
                                print(f"  [+] {move}")
                                
                        print("================================================\n")

                        baseline_state = current_state
                        is_settling = False
                        
                        print("Waiting for next movement...")

            time.sleep(0.05) 

    except KeyboardInterrupt:
        print("\nDetection script stopped safely.")

if __name__ == "__main__":
    main()