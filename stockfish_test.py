from stockfish import Stockfish

def main():
    # Replace this with the exact path from 'which stockfish'
    engine_path = "/usr/games/stockfish"

    # Initialize the Stockfish engine
    try:
        stockfish = Stockfish(path=engine_path)
    except Exception as e:
        print(f"Error loading Stockfish: {e}")
        return

    print("Engine loaded successfully!")
    
    # 1. Set the initial board using the standard starting FEN string
    starting_fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    stockfish.set_fen_position(starting_fen)
    
    print("\nInitial Board:")
    print(stockfish.get_board_visual())
    print("-" * 30)

    # 2. Update the board by making a move from that starting position
    moves = ["d2d4"]
    stockfish.make_moves_from_current_position(moves)
    
    print("\nBoard after e2-e4:")
    print(stockfish.get_board_visual())
    print("-" * 30)

    # Ask Stockfish for the best move response
    best_move = stockfish.get_best_move()
    print(f"\nStockfish suggests playing: {best_move}")

if __name__ == "__main__":
    main()