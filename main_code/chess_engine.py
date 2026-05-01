import chess
from stockfish import Stockfish
from gantry_control import GantryControl

class ChessEngine:
    def __init__(self):
        try:
            self.controller = GantryControl()
            self.controller.home_system()
        except Exception as e:
            print(f"Failed to initialize gantry controller. Error: {e}")
            return
            
        STOCKFISH_PATH = "stockfish"
        
        try:
            self.engine = Stockfish(path=STOCKFISH_PATH)
            self.engine.set_skill_level(10) 
            print("Stockfish engine connected successfully!")
        except Exception as e:
            print(f"Failed to find Stockfish executable. Error: {e}")
            return

        self.board = chess.Board()

    def get_move_from_events(self, lifts, places):
        """Translates raw physical board changes into a legal chess move using strict set matching."""
        possible_moves = []
        for move in self.board.legal_moves:
            expected_lifts = set()
            expected_places = set()
            
            start = chess.square_name(move.from_square)
            end = chess.square_name(move.to_square)
            
            # Base logic
            expected_lifts.add(start)
            expected_places.add(end)
            
            # 1. Castling Logic
            if self.board.is_castling(move):
                if end == "g1":   # White Kingside
                    expected_lifts.add("h1")
                    expected_places.add("f1")
                elif end == "c1": # White Queenside
                    expected_lifts.add("a1")
                    expected_places.add("d1")
                elif end == "g8": # Black Kingside
                    expected_lifts.add("h8")
                    expected_places.add("f8")
                elif end == "c8": # Black Queenside
                    expected_lifts.add("a8")
                    expected_places.add("d8")
                    
            # 2. En Passant Logic
            elif self.board.is_en_passant(move):
                ep_file = chess.square_file(move.to_square)
                ep_rank = chess.square_rank(move.from_square)
                victim_sq = chess.square_name(chess.square(ep_file, ep_rank))
                expected_lifts.add(victim_sq)
                
            # 3. Normal Capture Logic
            elif self.board.is_capture(move):
                expected_lifts.add(end)

            # Match exact lifts and places
            if lifts == expected_lifts and places == expected_places:
                possible_moves.append(move)
                
        if len(possible_moves) == 1:
            return possible_moves[0].uci()
        elif len(possible_moves) > 1:
            # Handle Promotions
            for m in possible_moves:
                if m.promotion == chess.QUEEN:
                    return m.uci()
            return possible_moves[0].uci()
        else:
            raise ValueError("Board layout does not exactly match any legal move.")

    def process_human_move(self, uci_str):
        move = chess.Move.from_uci(uci_str)
        san_notation = self.board.san(move)
        self.board.push(move)
        return san_notation

    def play_robot_turn(self):
        self.engine.set_fen_position(self.board.fen())
        best_move_uci = self.engine.get_best_move()
        sf_move = chess.Move.from_uci(best_move_uci)
        
        start_square = chess.square_name(sf_move.from_square)
        end_square = chess.square_name(sf_move.to_square)
        san_notation = self.board.san(sf_move)
        
        print(f"\n--- EXECUTING GANTRY SEQUENCE: {san_notation} ---")

        # A. Handle Castling 
        if self.board.is_castling(sf_move):
            if end_square == "g1":
                rook_start, rook_end = "h1", "f1"
            elif end_square == "c1":
                rook_start, rook_end = "a1", "d1"
            elif end_square == "g8":
                rook_start, rook_end = "h8", "f8"
            elif end_square == "c8":
                rook_start, rook_end = "a8", "d8"
                
            self.move_to_pos(start_square, end_square)
            self.move_to_pos(rook_start, rook_end)
            
        else:
            # B. Handle Captures
            if self.board.is_capture(sf_move):
                if self.board.is_en_passant(sf_move):
                    ep_file = chess.square_file(sf_move.to_square)
                    ep_rank = chess.square_rank(sf_move.from_square)
                    capture_square = chess.square_name(chess.square(ep_file, ep_rank))
                else:
                    capture_square = end_square
                
                self.move_to_captured(capture_square)

            # C. Move Main Piece
            self.move_to_pos(start_square, end_square)
            
        self.calibrate()
        self.board.push(sf_move)
        return best_move_uci, san_notation

    # --- GANTRY MOVEMENT FUNCTIONS ---

    def move_to_captured(self, capture_square):
        try:
            print(f"[GANTRY] Removing captured piece from {capture_square} to drop zone (0,0)")
            # 1. Edge-travel to capture square, dive center, grab, back to edge
            self.controller.move_to_square(capture_square)
            self.controller.corner_center(to_center=True)
            self.controller.electromagnet()
            self.controller.corner_center(to_center=False)
            
            # 2. Edge-travel to (0,0) drop zone, dive center, drop, back to edge
            self.controller.move_to_square("a1", True) 
            self.controller.corner_center(to_center=True)
            self.controller.electromagnet() 
            self.controller.corner_center(to_center=False)
        except Exception as e:
            print(f"Failed. Error: {e}")

    def move_to_pos(self, start_square, end_square):
        try:
            print(f"[GANTRY] Moving piece from {start_square} to {end_square}")
            # 1. Edge-travel to start, dive center, grab, back to edge
            self.controller.move_to_square(start_square)
            self.controller.corner_center(to_center=True)
            self.controller.electromagnet()
            self.controller.corner_center(to_center=False)
            
            # 2. Edge-travel to end, dive center, drop, back to edge
            self.controller.move_to_square(end_square)
            self.controller.corner_center(to_center=True)
            self.controller.electromagnet()
            self.controller.corner_center(to_center=False)
        except Exception as e:
            print(f"Failed. Error: {e}")

    def calibrate(self):
        try:    
            self.controller.home_system()
        except Exception as e:
            print(f"Failed. Error: {e}")
            
    def shutdown(self):
        try:
            self.controller.electromagnet_cleanup()
        except:
            pass