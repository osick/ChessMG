#!/usr/bin/env python3
"""
Demonstration of the improved chessmg API.

This example shows how the new API addresses the issues with the old API
and provides a much cleaner, more Pythonic interface.
"""

from chessmg import ChessPosition, Move, Color
import time


def print_section(title):
    """Helper to print section headers."""
    print(f"\n{'=' * 60}")
    print(f"{title:^60}")
    print('=' * 60)


def demo_old_vs_new_api():
    """Compare old and new API for move generation."""
    print_section("Old vs New API Comparison")
    
    print("\n### OLD API (Confusing) ###")
    from chessmg import ChessMoveGenerator
    old_pos = ChessMoveGenerator()
    
    # Old way: flat list where every 3 elements = 1 move
    old_moves = old_pos.moves(as_string=False)
    print(f"Old API returns flat list: {old_moves[:9]}")
    print("^ This means: move 1 = [57, 40, 0], move 2 = [57, 42, 0], etc.")
    print("Very confusing! Need to manually reshape.")
    
    print("\n### NEW API (Clear) ###")
    new_pos = ChessPosition()
    
    # New way: properly structured data
    new_moves_array = new_pos._engine.moves(as_string=False)  # If you need array
    print(f"New API with array: shape = {new_moves_array.shape}")
    print(f"First move as array: {new_moves_array[0]} = [from, to, flags]")
    
    # Even better: Move objects
    new_moves = new_pos.legal_moves()
    print(f"\nBetter yet, get Move objects:")
    for i, move in enumerate(new_moves[:3]):
        print(f"  Move {i+1}: {move} (from {move.from_square_name} to {move.to_square_name})")


def demo_move_objects():
    """Demonstrate the new Move object API."""
    print_section("Move Objects - Rich Information")
    
    pos = ChessPosition()
    moves = pos.legal_moves()
    
    # Show detailed information about moves
    print("\nDetailed move information:")
    example_moves = ["e2e4", "g1f3", "b1c3"]
    
    for uci in example_moves:
        move = next((m for m in moves if m.uci == uci), None)
        if move:
            print(f"\nMove: {move}")
            print(f"  UCI notation: {move.uci}")
            print(f"  From square: {move.from_square} ({move.from_square_name})")
            print(f"  To square: {move.to_square} ({move.to_square_name})")
            print(f"  Promotion: {move.promotion}")


def demo_game_play():
    """Demonstrate playing a game with the new API."""
    print_section("Playing a Game")
    
    game = ChessPosition()
    
    # Play a simple opening
    opening_moves = [
        "e2e4", "e7e5",
        "g1f3", "b8c6", 
        "f1c4", "g8f6",
        "d2d3", "f8c5"
    ]
    
    print("\nPlaying Italian Opening:")
    for i, move in enumerate(opening_moves):
        try:
            # Make the move
            game.make_move(move)
            
            # Show position info
            player = "White" if i % 2 == 0 else "Black"
            print(f"{player} plays: {move}")
            
        except ValueError as e:
            print(f"Illegal move {move}: {e}")
            break
    
    print(f"\nFinal position: {game.fen}")
    print(f"Next to move: {game.turn}")
    print(f"Is check: {game.is_check}")
    print(f"Legal moves: {len(game.legal_moves())}")


def demo_position_analysis():
    """Demonstrate position analysis features."""
    print_section("Position Analysis")
    
    # Set up a tactical position
    fen = "r1bqkb1r/pppp1ppp/2n2n2/1B2p3/4P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4"
    pos = ChessPosition(fen)
    
    print(f"\nPosition: {fen}")
    print(f"Turn: {pos.turn}")
    print(f"Is check: {pos.is_check}")
    print(f"Legal moves: {len(pos.legal_moves())}")
    
    # Show all legal moves grouped by piece
    print("\nLegal moves by starting square:")
    moves_by_square = {}
    for move in pos.legal_moves():
        from_sq = move.from_square_name
        if from_sq not in moves_by_square:
            moves_by_square[from_sq] = []
        moves_by_square[from_sq].append(move.to_square_name)
    
    for square, destinations in sorted(moves_by_square.items()):
        print(f"  {square}: {', '.join(destinations)}")


def demo_game_endings():
    """Demonstrate checkmate and stalemate detection."""
    print_section("Game Ending Detection")
    
    # Checkmate position (back rank mate)
    checkmate_fen = "6k1/5ppp/8/8/8/8/8/R6K b - - 0 1"
    pos = ChessPosition(checkmate_fen)
    
    print("\nCheckmate position:")
    print(f"FEN: {checkmate_fen}")
    print(f"Is checkmate: {pos.is_checkmate}")
    print(f"Is stalemate: {pos.is_stalemate}")
    print(f"Is game over: {pos.is_game_over}")
    print(f"Legal moves: {len(pos.legal_moves())}")
    
    # Stalemate position
    stalemate_fen = "7k/5Q2/6K1/8/8/8/8/8 b - - 0 1"
    pos = ChessPosition(stalemate_fen)
    
    print("\nStalemate position:")
    print(f"FEN: {stalemate_fen}")
    print(f"Is checkmate: {pos.is_checkmate}")
    print(f"Is stalemate: {pos.is_stalemate}")
    print(f"Is game over: {pos.is_game_over}")
    print(f"Legal moves: {len(pos.legal_moves())}")


def demo_performance():
    """Demonstrate the performance of move generation."""
    print_section("Performance Testing")
    
    pos = ChessPosition()
    
    # Warm up
    for _ in range(1000):
        pos.legal_moves()
    
    # Time move generation
    iterations = 100000
    start = time.time()
    
    for _ in range(iterations):
        moves = pos.legal_moves()
    
    elapsed = time.time() - start
    moves_per_second = (iterations * 20) / elapsed  # 20 moves in starting position
    
    print(f"\nGenerated {iterations:,} move lists in {elapsed:.2f} seconds")
    print(f"Performance: {moves_per_second:,.0f} moves/second")
    
    # Perft test
    print("\nPerft results (starting position):")
    for depth in range(1, 6):
        start = time.time()
        nodes = pos.perft(depth)
        elapsed = time.time() - start
        nps = nodes / elapsed if elapsed > 0 else 0
        print(f"  Depth {depth}: {nodes:>10,} nodes in {elapsed:>5.2f}s ({nps:>12,.0f} NPS)")


def demo_undo_redo():
    """Demonstrate undo/redo functionality."""
    print_section("Undo/Redo Moves")
    
    game = ChessPosition()
    moves_played = []
    
    # Play some moves
    moves_to_play = ["e2e4", "e7e5", "g1f3", "b8c6"]
    
    print("\nPlaying moves:")
    for move in moves_to_play:
        game.make_move(move)
        moves_played.append(move)
        print(f"  Played: {move}")
    
    print(f"\nPosition after moves: {game.fen}")
    
    # Undo all moves
    print("\nUndoing moves:")
    while moves_played:
        undone = game.undo_move()
        if undone:
            print(f"  Undid: {undone}")
            moves_played.pop()
    
    print(f"\nBack to starting position: {game.fen}")


def main():
    """Run all demonstrations."""
    print("chessmg Improved API Demonstration")
    print("==================================")
    
    demos = [
        demo_old_vs_new_api,
        demo_move_objects,
        demo_game_play,
        demo_position_analysis,
        demo_game_endings,
        demo_undo_redo,
        demo_performance,
    ]
    
    for demo in demos:
        try:
            demo()
        except Exception as e:
            print(f"\nError in {demo.__name__}: {e}")
    
    print("\n" + "=" * 60)
    print("Demonstration complete!")


if __name__ == "__main__":
    main()