from pycmg import Pos

position = Pos("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")

print("List of all moves in the starting position")

[print(p) for p in position.get_w_moves(as_string=True)]