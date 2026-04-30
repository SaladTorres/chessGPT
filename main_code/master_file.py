from expanders import ChessSensors
from chess_engine import ChessEngine
import time

def main():
    # 1. Define the objects INSIDE main
    sensors = ChessSensors()
    engine = ChessEngine()
    move_history = []
    
    # Initialize states
    last_confirmed_state = sensors.get_board_dict()
    last_seen_state = last_confirmed_state
    stable_start_time = time.time()
    
    print("System Online. Awaiting your move...")

    # 2. The loop MUST be indented to stay inside main()
    while True:
        current_state = sensors.get_board_dict() # This now sees 'sensors'

        if current_state != last_seen_state:
            last_seen_state = current_state
            stable_start_time = time.time()
            # print("Movement detected...") # Optional: noisy for debugging

        elif (time.time() - stable_start_time > 3.0) and (current_state != last_confirmed_state):
            from_square = None
            to_square = None

            for square in sensors.square_map:
                if "cap" in square: continue
                
                if last_confirmed_state[square] == 1 and current_state[square] == 0:
                    from_square = square
                elif last_confirmed_state[square] == 0 and current_state[square] == 1:
                    to_square = square

            if from_square and to_square:
                user_move = f"{from_square}{to_square}"
                print(f"--- MOVE STABILIZED: {user_move} ---")
                
                move_history.append(user_move)
                stockfish_move = engine.get_best_move(move_history)
                print(f"Stockfish counter-move: {stockfish_move}")
                
                move_history.append(stockfish_move)
                
                # Update the confirmation state
                last_confirmed_state = current_state
            
        time.sleep(0.1)

# 3. This is what actually starts the code
if __name__ == "__main__":
    main()