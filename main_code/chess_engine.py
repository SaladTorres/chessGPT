from stockfish import Stockfish

class ChessEngine:
    def __init__(self, path="/usr/games/stockfish"):
        self.stockfish = Stockfish(path=path)

    def get_best_move(self, move_history):
        """
        Resets Stockfish to the start and replays the entire history.
        """
        try:
            # 1. Reset to standard starting position (Hardcoded string)
            self.stockfish.set_fen_position("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
            
            # 2. Play the full list of moves from the start
            if move_history and len(move_history) > 0:
                self.stockfish.make_moves_from_current_position(move_history)
            
            # 3. Get the best move
            move = self.stockfish.get_best_move()
            return move
            
        except Exception as e:
            print(f"Stockfish processing error: {e}")
            return None