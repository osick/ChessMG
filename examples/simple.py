from chessmg import ChessMoveGenerator
import numpy as np
position = ChessMoveGenerator("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")

start_moves=np.reshape(np.array(position.moves(as_string=False), dtype=int), (-1,3))
print("List of all moves in the starting position")
print(start_moves) # list of moves: (from, to, move_flag)