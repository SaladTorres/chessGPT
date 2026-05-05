from expanders import ChessSensors
from chess_engine import ChessEngine
import time
import sys
import re
import chess 

class MockSensors:
    def __init__(self):
        self.square_map = [
            "a1","a2","a3","a4","a5","a6","a7","a8", "b1","b2","b3","b4","b5","b6","b7","b8",
            "c1","c2","c3","c4","c5","c6","c7","c8", "d1","d2","d3","d4","d5","d6","d7","d8",
            "e1","e2","e3","e4","e5","e6","e7","e8", "f1","f2","f3","f4","f5","f6","f7","f8",
            "g1","g2","g3","g4","g5","g6","g7","g8", "h1","h2","h3","h4","h5","h6","h7","h8",
            "cap1","cap2","cap3","cap4","cap5","cap6","cap7","cap8",
            "nc1","nc2","nc3","nc4","nc5","nc6","nc7","nc8"
        ]
        self.state = {sq: 0 for sq in self.square_map}
        for col in "abcdefgh":
            for row in ["1", "2", "7", "8"]:
                self.state[col + row] = 1

    def get_board_dict(self):
        return self.state.copy()

    def apply_san_move(self, move, board):
        start_sq = chess.square_name(move.from_square)
        end_sq = chess.square_name(move.to_square)

        self.state[start_sq] = 0
        self.state[end_sq] = 1

        if board.is_castling(move):
            if end_sq == "g1": self.state["h1"], self.state["f1"] = 0, 1
            elif end_sq == "c1": self.state["a1"], self.state["d1"] = 0, 1
            elif end_sq == "g8": self.state["h8"], self.state["f8"] = 0, 1
            elif end_sq == "c8": self.state["a8"], self.state["d8"] = 0, 1
        elif board.is_en_passant(move):
            ep_file = chess.square_file(move.to_square)
            ep_rank = chess.square_rank(move.from_square)
            victim_sq = chess.square_name(chess.square(ep_file, ep_rank))
            self.state[victim_sq] = 0
            
        print(f"[*] Digital Update: Simulated physical board changes for {board.san(move)}")


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
    
    # Track mid-move lifts so we don't miss captures
    transient_lifts = set()

    print("\nSystem Online. White (Human) to move...")

    try:
        while True:
            # --- DIGITAL MODE LOOP ---
            if digital:
                cmd = input("\nEnter your move (e.g., 'e4', 'Nf3', 'O-O') or 'q' to quit: ")
                if cmd.lower() == 'q': break
                
                try:
                    parsed_move = engine.board.parse_san(cmd)
                    
                    # SIMULATE PHYSICAL CAPTURE: The victim piece is removed first mid-move
                    if engine.board.is_capture(parsed_move) and not engine.board.is_en_passant(parsed_move):
                        transient_lifts.add(chess.square_name(parsed_move.to_square))
                        
                    sensors.apply_san_move(parsed_move, engine.board)
                    
                    current_state = sensors.get_board_dict()
                    last_seen_state = current_state.copy() 
                    stable_start_time = time.time() - 4.0 
                except ValueError:
                    print("[!] Invalid notation or illegal move. Try again.")
                    continue

            # --- PHYSICAL MODE LOOP ---
            else:
                try:
                    current_state = sensors.get_board_dict()
                except OSError:
                    time.sleep(0.1)
                    continue 

                if current_state != last_seen_state:
                    # PHYSICAL CAPTURE TRACKING: Log any square that momentarily loses its piece
                    for sq in sensors.square_map:
                        if last_seen_state[sq] == 1 and current_state[sq] == 0:
                            transient_lifts.add(sq)
                            
                    last_seen_state = current_state.copy()
                    stable_start_time = time.time()

            # --- SHARED MOVE PROCESSING LOGIC ---
            if time.time() - stable_start_time > 3.0:
                
                if current_state != last_confirmed_state:
                    active_lifts = set()
                    active_places = set()
                    
                    for sq in sensors.square_map:
                        if "cap" in sq or "nc" in sq: continue 
                        
                        # 1. Normal Lifts (1 -> 0)
                        if last_confirmed_state[sq] == 1 and current_state[sq] == 0: 
                            active_lifts.add(sq)
                            
                        # 2. Normal Places (0 -> 1)
                        elif last_confirmed_state[sq] == 0 and current_state[sq] == 1: 
                            active_places.add(sq)
                            
                        # 3. Captures (1 -> 0 mid-move -> 1)
                        elif sq in transient_lifts and last_confirmed_state[sq] == 1 and current_state[sq] == 1:
                            active_lifts.add(sq)  # The victim piece was removed
                            active_places.add(sq) # The attacking piece was placed
                    
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

                            if not digital:
                                time.sleep(1.0)
                                current_state = sensors.get_board_dict()
                            else:
                                # Re-sync hardware/software after gantry moves pieces
                                sf_move_obj = chess.Move.from_uci(sf_uci)
                                engine.board.pop() 
                                sensors.apply_san_move(sf_move_obj, engine.board)
                                engine.board.push(sf_move_obj) 
                                current_state = sensors.get_board_dict()
                                
                            last_seen_state = current_state.copy()
                            last_confirmed_state = current_state.copy()
                            transient_lifts.clear() # RESET for next turn
                            stable_start_time = time.time()
                            
                            print("\nYour turn again! (White)")
                            
                        except ValueError as e:
                            print(f"[!] Board mismatch: {e}")
                            print("Please correct the board. Waiting for legal state...")
                    else:
                        last_confirmed_state = current_state.copy()
                        transient_lifts.clear() # Clear fumbles
                        
            if not digital:
                time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\nShutting down gracefully...")
    finally:
        engine.shutdown()

if __name__ == "__main__":
    main(digital=True)