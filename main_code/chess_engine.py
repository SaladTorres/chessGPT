from stockfish import Stockfish

class ChessEngine:
    def __init__(self, path="/usr/games/stockfish"):
        self.stockfish = Stockfish(path=path)
        self.stockfish.set_fen_position("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")

    def get_best_move(self, move_history):
        self.stockfish.make_moves_from_current_position(move_history)
        return self.stockfish.get_best_move()