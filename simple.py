from libpycmg import Pos
position = Pos("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
print(position.get_w_moves(as_string=True))