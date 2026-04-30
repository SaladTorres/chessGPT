import chess
from stockfish import Stockfish
from gantry_control import GantryControl

class ChessEngine:
    def __init__(self):
        # --- GANTRY SETUP ---
        try:
            self.controller = GantryControl()
            self.controller.home_system()
        except Exception as e:
            print(f"Failed to initialize gantry controller. Error: {e}")
            return
        # --- ENGINE SETUP ---
        STOCKFISH_PATH = "stockfish"
        
        try:
            # Initialize the pip stockfish wrapper
            self.engine = Stockfish(path=STOCKFISH_PATH)
            self.engine.set_skill_level(10) # Set difficulty (0-20)
            print("Stockfish engine connected successfully!")
        except Exception as e:
            print(f"Failed to find Stockfish executable. Error: {e}")
            return

        # Initialize the digital board referee
        self.board = chess.Board()
        capture_square_index = 1

    def move_to_captured(self, capture_square, capture_index):
        """
        Moves the gantry to pick up a captured piece from its square and drop it in the graveyard.
        """
        try:
            print(f"[GANTRY] Moving captured piece on {capture_square} to capture square {capture_index}")
            self.controller.move_to_square(capture_square)
            self.controller.corner_center(to_center=True)
            self.controller.electromagnet()
            self.controller.corner_center(to_center=False)
            self.controller.move_to_square("h8") #change with capture index squares
            self.controller.corner_center(to_center=True)
            self.controller.electromagnet()
            self.controller.corner_center(to_center=False)
        except Exception as e:
            print(f"Failed. Error: {e}")
            return

    def move_to_pos(self, start_square, end_square):
        """
        Moves the gantry to pick up the active piece and move it to its new square.
        """
        try:
            print(f"[GANTRY] Moving piece from {start_square} to {end_square}")
            self.controller.move_to_square(start_square)
            self.controller.corner_center(to_center=True)
            self.controller.electromagnet()
            self.controller.corner_center(to_center=False)
            self.controller.move_to_square(end_square)
            self.controller.corner_center(to_center=True)
            self.controller.electromagnet()
            self.controller.corner_center(to_center=False)
        except Exception as e:
            print(f"Failed. Error: {e}")
            return

    def calibrate(self):
        """
        Runs the physical homing sequence.
        """
        
        try:    
            self.controller.home_system()
            print("[GANTRY] Calibrating gantry to X=0, Y=0...")
        except Exception as e:
            print(f"Failed. Error: {e}")
            return

    # --- MAIN CHESS LOGIC ---

    def play_game(self):

        print("\n--- NEW GAME STARTED ---")
        print(self.board)
        print("------------------------\n")

        try:
            while not self.board.is_game_over():
                # 1. PLAYER TURN (White)
                user_move_str = input("Enter your move (e.g., e2e4, Nf3) or 'q' to quit: ")
                
                if user_move_str.lower() == 'q':
                    break
                    
                try:
                    # The chess library safely parses notation and updates the digital board
                    user_move = self.board.parse_san(user_move_str)
                    self.board.push(user_move)
                except ValueError:
                    print("Invalid move. Try again.")
                    continue

                print("\nBoard after your move:")
                print(self.board)
                print("-" * 30)

                if self.board.is_game_over():
                    break

                # 2. STOCKFISH TURN (Black)
                print("\nStockfish is thinking...")
                
                # Sync the stockfish library with our digital board referee
                self.engine.set_fen_position(self.board.fen())
                
                # Ask the stockfish pip library for the best move string (e.g., "d5e4")
                best_move_uci = self.engine.get_best_move()
                sf_move = chess.Move.from_uci(best_move_uci)
                
                # Extract clean start/end coordinates for the main moving piece
                start_square = chess.square_name(sf_move.from_square)
                end_square = chess.square_name(sf_move.to_square)

                print(f"\nStockfish plays: {self.board.san(sf_move)} ({start_square} to {end_square})")
                print("--- EXECUTING GANTRY SEQUENCE ---")

                # A. Check for Captures using the digital board referee
                if self.board.is_capture(sf_move):
                    if self.board.is_en_passant(sf_move):
                        # In En Passant, the captured pawn is on the same file as the destination square,
                        # but on the same rank as the starting square!
                        ep_file = chess.square_file(sf_move.to_square)
                        ep_rank = chess.square_rank(sf_move.from_square)
                        capture_square = chess.square_name(chess.square(ep_file, ep_rank))
                    else:
                        # Normal capture: the piece being taken is sitting on the destination square
                        capture_square = end_square
                    
                    # Execute Capture Placeholder
                    self.move_to_captured(capture_square, capture_square_index)
                    capture_square_index += 1

                # B. Move the main piece Placeholder
                self.move_to_pos(start_square, end_square)
                
                # C. Calibrate Placeholder
                self.calibrate()

                print("---------------------------------")
                
                # Finally, update the digital board referee with Stockfish's move
                self.board.push(sf_move)
                print("\nBoard after Stockfish:")
                print(self.board)
                print("-" * 30)

        except KeyboardInterrupt:
            print("\nGame aborted.")
        finally:
            print("Game closed.")

if __name__ == "__main__":
    engine = ChessEngine()
    engine.play_game()