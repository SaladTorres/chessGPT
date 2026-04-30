import chess
from stockfish import Stockfish

# --- GANTRY PLACEHOLDER FUNCTIONS ---

def move_to_captured(capture_square, capture_index):
    """
    Moves the gantry to pick up a captured piece from its square and drop it in the graveyard.
    """
    print(f"[GANTRY] Moving captured piece on {capture_square} to capture square {capture_index}")

def move_to_pos(start_square, end_square):
    """
    Moves the gantry to pick up the active piece and move it to its new square.
    """
    print(f"[GANTRY] Moving piece from {start_square} to {end_square}")

def calibrate():
    """
    Runs the physical homing sequence.
    """
    print("[GANTRY] Calibrating gantry to X=0, Y=0...")

# --- MAIN CHESS LOGIC ---

def play_game():
    # --- ENGINE SETUP ---
    STOCKFISH_PATH = "stockfish"
    
    try:
        # Initialize the pip stockfish wrapper
        engine = Stockfish(path=STOCKFISH_PATH)
        engine.set_skill_level(10) # Set difficulty (0-20)
        print("Stockfish engine connected successfully!")
    except Exception as e:
        print(f"Failed to find Stockfish executable. Error: {e}")
        return

    # Initialize the digital board referee
    board = chess.Board()
    capture_square_index = 1
    
    print("\n--- NEW GAME STARTED ---")
    print(board)
    print("------------------------\n")

    try:
        while not board.is_game_over():
            # 1. PLAYER TURN (White)
            user_move_str = input("Enter your move (e.g., e2e4, Nf3) or 'q' to quit: ")
            
            if user_move_str.lower() == 'q':
                break
                
            try:
                # The chess library safely parses notation and updates the digital board
                user_move = board.parse_san(user_move_str)
                board.push(user_move)
            except ValueError:
                print("Invalid move. Try again.")
                continue

            print("\nBoard after your move:")
            print(board)
            print("-" * 30)

            if board.is_game_over():
                break

            # 2. STOCKFISH TURN (Black)
            print("\nStockfish is thinking...")
            
            # Sync the stockfish library with our digital board referee
            engine.set_fen_position(board.fen())
            
            # Ask the stockfish pip library for the best move string (e.g., "d5e4")
            best_move_uci = engine.get_best_move()
            sf_move = chess.Move.from_uci(best_move_uci)
            
            # Extract clean start/end coordinates for the main moving piece
            start_square = chess.square_name(sf_move.from_square)
            end_square = chess.square_name(sf_move.to_square)

            print(f"\nStockfish plays: {board.san(sf_move)} ({start_square} to {end_square})")
            print("--- EXECUTING GANTRY SEQUENCE ---")

            # A. Check for Captures using the digital board referee
            if board.is_capture(sf_move):
                if board.is_en_passant(sf_move):
                    # In En Passant, the captured pawn is on the same file as the destination square,
                    # but on the same rank as the starting square!
                    ep_file = chess.square_file(sf_move.to_square)
                    ep_rank = chess.square_rank(sf_move.from_square)
                    capture_square = chess.square_name(chess.square(ep_file, ep_rank))
                else:
                    # Normal capture: the piece being taken is sitting on the destination square
                    capture_square = end_square
                
                # Execute Capture Placeholder
                move_to_captured(capture_square, capture_square_index)
                capture_square_index += 1

            # B. Move the main piece Placeholder
            move_to_pos(start_square, end_square)
            
            # C. Calibrate Placeholder
            calibrate()

            print("---------------------------------")
            
            # Finally, update the digital board referee with Stockfish's move
            board.push(sf_move)
            print("\nBoard after Stockfish:")
            print(board)
            print("-" * 30)

    except KeyboardInterrupt:
        print("\nGame aborted.")
    finally:
        print("Game closed.")

if __name__ == "__main__":
    play_game()