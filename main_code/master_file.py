from expanders import ChessSensors
from chess_engine import ChessEngine
import time
import sys
import re
import chess

class MockSensors:
    """A digital twin of the physical chess board for testing."""
    def __init__(self):
        self.square_map = [
            "a1","a2","a3","a4","a5","a6","a7","a8", "b1","b2","b3","b4","b5","b6","b7","b8",
            "c1","c2","c3","c4","c5","c6","c7","c8", "d1","d2","d3","d4","d5","d6","d7","d8",
            "e1","e2","e3","e4","e5","e6","e7","e8", "f1","f2","f3","f4","f5","f6","f7","f8",
            "g1","g2","g3","g4","g5","g6","g7","g8", "h1","h2","h3","h4","h5","h6","h7","h8",
            "cap1","cap2","cap3","cap4","cap5","cap6","cap7","cap8",
            "nc1","nc2","nc3","nc4","nc5","nc6","nc7","nc8"
        ]
        
        # Initialize the perfect starting board
        self.state = {sq: 0 for sq in self.square_map}
        for col in "abcdefgh":
            for row in ["1", "2", "7", "8"]:
                self.state[col + row] = 1

    def get_board_dict(self):
        return self.state.copy()

    def pin_to_square(self, pin_str, board_num):
        """Converts 'PA1' and '26' into 'g2'."""
        board_idx = int(board_num) - 23
        if board_idx < 0 or board_idx > 4:
            raise ValueError(f"Invalid board: {board_num}. Must be 23-27.")
            
        pin_str = pin_str.upper()
        if pin_str.startswith("PA"):
            pin_idx = int(pin_str[2:])
        elif pin_str.startswith("PB"):
            pin_idx = int(pin_str[2:]) + 8
        else:
            raise ValueError(f"Invalid pin format: {pin_str}. Must be PA0-PA7 or PB0-PB7.")
            
        return self.square_map[(board_idx * 16) + pin_idx]

    def execute_command(self, cmd):
        """Parses the command and updates the digital state."""
        # e.g., "move PA1 on 26 to PB2 on 25"
        pattern = r"move\s+(P[AB]\d)\s+on\s+(\d+)\s+to\s+(P[AB]\d)\s+on\s+(\d+)"
        match = re.search(pattern, cmd, re.IGNORECASE)
        
        if match:
            src_pin, src_brd, dst_pin, dst_brd = match.groups()
            src_sq = self.pin_to_square(src_pin, src_brd)
            dst_sq = self.pin_to_square(dst_pin, dst_brd)
            
            # Physically "lift" from source and "place" at destination
            self.state[src_sq] = 0
            self.state[dst_sq] = 1
            print(f"[*] Digital Update: Moved piece from {src_sq} to {dst_sq}")
            return True
        else:
            print("[!] Invalid command format. Example: 'move PA1 on 26 to PB2 on 25'")
            return False


def validate_starting_board(sensors, expected_state):
    print("\n--- RUNNING STARTUP AUDIT ---")
    print("Verifying physical board matches the 32 starting pieces...")
    
    while True:
        try:
            current = sensors.get_board_dict()
        except OSError:
            time.sleep(0.1)
            continue
            
        missing, extra = [], []
        for sq in sensors.square_map:
            if "cap" in sq or "nc" in sq: continue 
            if expected_state[sq] == 1 and current[sq] == 0: missing.append(sq)
            elif expected_state[sq] == 0 and current[sq] == 1: extra.append(sq)
                
        if not missing and not extra:
            print("Audit Passed! Board is perfectly synced.")
            break
        else:
            sys.stdout.write("\r[!] Discrepancy detected. Please check wires...   ")
            sys.stdout.flush()
            if missing: print(f"\n    -> MISSING piece (ground wire) on: {', '.join(missing)}")
            if extra: print(f"    -> EXTRA piece (unexpected ground) on: {', '.join(extra)}")
            time.sleep(1.5)
            sys.stdout.write("\033[F\033[K" * (2 + (1 if missing else 0) + (1 if extra else 0)))


def main(digital=False):
    try:
        # Toggle between physical I2C hardware and our new Digital Mock
        if digital:
            print("--- RUNNING IN DIGITAL MOCK MODE ---")
            sensors = MockSensors()
        else:
            sensors = ChessSensors()
            
        engine = ChessEngine()
    except Exception as e:
        print(f"Initialization failed: {e}")
        return

    full_start = {sq: 0 for sq in sensors.square_map}
    for col in "abcdefgh":
        for row in ["1", "2", "7", "8"]:
            full_start[col + row] = 1
            
    if not digital:
        validate_starting_board(sensors, full_start)
    
    last_confirmed_state = full_start.copy()
    last_seen_state = sensors.get_board_dict()
    stable_start_time = time.time()

    print("\nSystem Online. White (Human) to move...")

    try:
        while True:
            # --- DIGITAL MODE LOOP ---
            if digital:
                cmd = input("\nEnter hardware command (or 'q' to quit): ")
                if cmd.lower() == 'q':
                    break
                
                # If command is valid, immediately set current_state and trigger the logic
                if sensors.execute_command(cmd):
                    current_state = sensors.get_board_dict()
                    last_seen_state = current_state.copy() 
                    # Fake the timer so it processes immediately
                    stable_start_time = time.time() - 4.0 
                else:
                    continue

            # --- PHYSICAL MODE LOOP ---
            else:
                try:
                    current_state = sensors.get_board_dict()
                except OSError:
                    time.sleep(0.1)
                    continue 

                if current_state != last_seen_state:
                    last_seen_state = current_state.copy()
                    stable_start_time = time.time()

            # --- SHARED MOVE PROCESSING LOGIC ---
            if time.time() - stable_start_time > 3.0:
                
                if current_state != last_confirmed_state:
                    active_lifts = set()
                    active_places = set()
                    
                    for sq in sensors.square_map:
                        if "cap" in sq or "nc" in sq: continue 
                        if last_confirmed_state[sq] == 1 and current_state[sq] == 0: active_lifts.add(sq)
                        elif last_confirmed_state[sq] == 0 and current_state[sq] == 1: active_places.add(sq)
                    
                    if active_lifts or active_places:
                        print(f"\n[DEBUG] Detected Lifts: {active_lifts}")
                        print(f"[DEBUG] Detected Places: {active_places}")
                        
                        try:
                            detected_uci = engine.get_move_from_events(active_lifts, active_places)
                            human_san = engine.process_human_move(detected_uci)
                            
                            print(f"\n[HUMAN] Move Finalized: {human_san} ({detected_uci})")
                            last_confirmed_state = current_state.copy()
                            
                            print("Stockfish is calculating and moving...")
                            sf_uci, sf_san = engine.play_robot_turn()
                            print(f"\n[ROBOT] Move Completed: {sf_san} ({sf_uci})")

                            # Re-sync hardware after gantry moves pieces (or sync mock board)
                            if not digital:
                                time.sleep(1.0)
                                current_state = sensors.get_board_dict()
                            else:
                                # In digital mode, Stockfish physically moved a piece on the real board,
                                # so we must update our mock digital board to reflect Stockfish's move
                                # otherwise the next turn will see ghost lifts!
                                sf_move_obj = chess.Move.from_uci(sf_uci)
                                sensors.state[chess.square_name(sf_move_obj.from_square)] = 0
                                sensors.state[chess.square_name(sf_move_obj.to_square)] = 1
                                current_state = sensors.get_board_dict()
                                
                            last_seen_state = current_state.copy()
                            last_confirmed_state = current_state.copy()
                            stable_start_time = time.time()
                            
                            print("\nYour turn again! (White)")
                            
                        except ValueError as e:
                            print(f"[!] Board mismatch: {e}")
                            print("Please correct the board. Waiting for legal state...")
                    else:
                        last_confirmed_state = current_state.copy()
                        
            if not digital:
                time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\nShutting down gracefully...")
    finally:
        engine.shutdown()

if __name__ == "__main__":
    # Change to digital=False when you plug the I2C hardware back in!
    main(digital=True)