from timeit import timeit
from time import time

from pycmg import perft

def perft_start_fen(depth):
    fen="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    start=time();  nodes = perft(fen,depth); duration=time()-start
    print(f"perft({depth})={nodes}")
    print(f"NPS={int(round(nodes/duration,0)):<15_},{duration=:<6.1f}")

if __name__ =="__main__":
    for depth in range(1,8):
        perft_start_fen(depth=depth)