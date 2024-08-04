import sys
from time import time

from pycmg import perft

def perft_time(fen,depth):
    start=time();  nodes = perft(fen,depth); duration=time()-start
    print(f"perft({depth})={nodes:<20,} | {f'{int(round(nodes/duration,0)):,}'+' NPS':16} | {duration:.1f} seconds")

if __name__ =="__main__":
    maxdepth=7
    if len(sys.argv)>=2:
        if sys.argv[1].isdigit(): maxdepth=max(1,int(sys.argv[1]))
    fen="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"

    title="perft results for chess starting position up to depth "+str(maxdepth)
    print("\n "+title+"\n"+"="*(len(title)+2))

    for depth in range(1,maxdepth+1):
        perft_time(fen=fen , depth=depth)