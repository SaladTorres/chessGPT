import time
import board
import digitalio

# --- CONFIGURATION ---
# Change D18 to whichever Raspberry Pi GPIO pin is wired to your magnet's MOSFET/Relay
# For example, if it's GPIO 23, use board.D23
MAGNET_PIN = board.D21

def main():
    # Set up the pin
    magnet = digitalio.DigitalInOut(MAGNET_PIN)
    magnet.direction = digitalio.Direction.OUTPUT

    try:
        print(f"[HARDWARE] Turning magnet ON (Pin {MAGNET_PIN} HIGH)")
        magnet.value = True
        
        print("Electromagnet is holding. Press Ctrl+C to release and exit.")
        
        # Keep the script alive so the magnet stays on
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n[HARDWARE] Manual interrupt detected.")
    finally:
        # SAFETY: Always ensure the magnet is turned off when exiting
        print("[HARDWARE] Turning magnet OFF (Pin LOW)")
        magnet.value = False
        magnet.deinit()
        print("Safe shutdown complete.")

if __name__ == "__main__":
    main()