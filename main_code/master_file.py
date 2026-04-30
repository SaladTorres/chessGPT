from expanders import ChessSensors
from chess_engine import ChessEngine
import time

def main():
    try:
        sensors = ChessSensors()
        engine = ChessEngine()
    except Exception as e:
        print(f"Initialization failed: {e}")
        return

    move_history = []


    
    # 1. SETUP VIRTUAL BOARD
    full_start = {sq: 0 for sq in sensors.square_map}
    for col in "abcdefgh":
        for row in ["1", "2", "7", "8"]:
            full_start[col + row] = 1
    
    last_confirmed_state = full_start 
    last_seen_state = sensors.get_board_dict()
    stable_start_time = time.time()
    
    current_turn = "HUMAN"
    pending_stockfish_move = None
    
    active_lift = None
    active_place = None
    victim_square = None

    print("System Online. White (Human) to move...")

    while True:
        try:
            current_state = sensors.get_board_dict()
        except OSError:
            time.sleep(0.1)
            continue 

        # 2. MONITOR PHYSICAL CHANGES
        if current_state != last_seen_state:
            for square in sensors.square_map:
                # --- CAPTURE DETECTION ---
                if "cap" in square:
                    if last_seen_state[square] == 0 and current_state[square] == 1:
                        # Find which square was emptied (excluding the attacker's start)
                        for s in sensors.square_map:
                            if "cap" in s: continue
                            if last_confirmed_state[s] == 1 and current_state[s] == 0 and s != active_lift:
                                victim_square = s
                                print(f"CAPTURE DETECTED: Piece removed from {victim_square}")
                
                # --- MOVEMENT DETECTION ---
                else:
                    if last_seen_state[square] == 1 and current_state[square] == 0:
                        if square != victim_square:
                            active_lift = square
                            print(f"DEBUG: Piece lifted from {active_lift}")
                    
                    elif last_seen_state[square] == 0 and current_state[square] == 1:
                        active_place = square
                        print(f"DEBUG: Piece placed on {active_place}")

            last_seen_state = current_state.copy()
            stable_start_time = time.time()

        # 3. PROCESS FINALIZED MOVES (Stable for 3 seconds)
        elif (time.time() - stable_start_time > 3.0) and active_lift and active_place:
            
            # Undo Logic: If piece put back where it started
            if active_lift == active_place:
                active_lift = None
                active_place = None
                victim_square = None
                continue

            detected_move = f"{active_lift}{active_place}"

            # --- HUMAN TURN ---
            if current_turn == "HUMAN":
                print(f"\n[HUMAN] Move Finalized: {detected_move}")
                try:
                    move_history.append(detected_move)
                    pending_stockfish_move = engine.get_best_move(move_history)
                    
                    if pending_stockfish_move:
                        # Update Virtual Board
                        if victim_square:
                            last_confirmed_state[victim_square] = 0
                        last_confirmed_state[active_lift] = 0
                        last_confirmed_state[active_place] = 1
                        
                        print(f"Stockfish response: {pending_stockfish_move}")
                        print(f">>> ACTION REQUIRED: Move Black {pending_stockfish_move}")
                        current_turn = "ROBOT"
                except ValueError:
                    print(f"Illegal Move: {detected_move}. Reset the board.")
                    move_history.pop()

            # --- ROBOT TURN ---
            elif current_turn == "ROBOT":
                if detected_move == pending_stockfish_move:
                    print(f"\n[ROBOT] Move confirmed: {detected_move}")
                    move_history.append(pending_stockfish_move)
                    
                    # Update Virtual Board
                    if victim_square:
                        last_confirmed_state[victim_square] = 0
                    last_confirmed_state[active_lift] = 0
                    last_confirmed_state[active_place] = 1
                    
                    current_turn = "HUMAN"
                    print("\nYour turn again! (White)")
                else:
                    print(f"Waiting for {pending_stockfish_move}. You moved {detected_move}")

            # Reset tracking for next turn
            active_lift = None
            active_place = None
            victim_square = None
                
        time.sleep(0.1)

if __name__ == "__main__":
    main()