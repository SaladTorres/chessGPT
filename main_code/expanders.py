import time
import board
import busio
import digitalio

from adafruit_mcp230xx.mcp23017 import MCP23017

class ChessSensors:
    def __init__(self):
        self.i2c = busio.I2C(board.SCL, board.SDA)
        self.addresses = [0x23, 0x24, 0x25, 0x26, 0x27]
        self.all_pins = []

        # Vertical Mapping: Each board handles 2 columns (16 rows total)
        self.square_map = [
            # 0x23: A & B
            "a1","a2","a3","a4","a5","a6","a7","a8", "b1","b2","b3","b4","b5","b6","b7","b8",
            # 0x24: C & D
            "c1","c2","c3","c4","c5","c6","c7","c8", "d1","d2","d3","d4","d5","d6","d7","d8",
            # 0x25: E & F
            "e1","e2","e3","e4","e5","e6","e7","e8", "f1","f2","f3","f4","f5","f6","f7","f8",
            # 0x26: G & H
            "g1","g2","g3","g4","g5","g6","g7","g8", "h1","h2","h3","h4","h5","h6","h7","h8",
            # 0x27: 8 Capture Zones + 8 Unused/Not Connected pins
            "cap1","cap2","cap3","cap4","cap5","cap6","cap7","cap8",
            "nc1","nc2","nc3","nc4","nc5","nc6","nc7","nc8"
        ]

        print("Initializing 80 sensors across 5 boards...")
        for addr in self.addresses:
            try:
                mcp = MCP23017(self.i2c, address=addr)
                for i in range(16):
                    p = mcp.get_pin(i)
                    p.direction = digitalio.Direction.INPUT
                    p.pull = digitalio.Pull.UP
                    self.all_pins.append(p)
            except Exception as e:
                print(f"Error connecting to board {hex(addr)}: {e}")

    def get_raw_states(self):
        return ["1" if not pin.value else "0" for pin in self.all_pins]

    def get_board_dict(self):
        raw = self.get_raw_states()
        return {self.square_map[i]: int(raw[i]) for i in range(80)}

    def run_live_dashboard(self):
        print("\n--- LIVE SENSOR GRID (1=PIECE, 0=EMPTY) ---")
        try:
            while True:
                try:
                    results = self.get_raw_states()
                    display = " | ".join(["".join(results[i:i+16]) for i in range(0, 80, 16)])
                    print(f"\rBoard (23|24|25|26|27): {display}", end="", flush=True)
                    time.sleep(0.05)
                except OSError:
                    print(f"  ! I2C Communication dropped.")
                    continue 
        except KeyboardInterrupt:
            print("\nDashboard stopped.")

if __name__ == "__main__":
    sensors = ChessSensors()
    sensors.run_live_dashboard()