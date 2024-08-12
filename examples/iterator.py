from chessmg import ChessMoveGenerator, PC, SQ
from time import time
import json
import os

def iter2():
    fen="8/5q2/Q7/8/8/8/8/K1k5 w - - 0 1"
    input = {"raw":[(13,2), (5,0) , (4,40), (12,53)], "turn":True, "epsq":64, "castling":""} #
    pos = ChessMoveGenerator(input)
    total= len(pos.moves())//3
    start=time()
    rounds=64*64*10
    for k in range(rounds):
        this = 0
        for i in range(0,63):
            next=i+1
            if next not in [2,40,53]:
                pos.move_piece(this,next)
                this  = next
                s=pos.state(0)
                mvs   = pos.moves()
                nodes = len(mvs)//3
                total+=nodes
                #if k==0: print(f"K{SQ(next).name}", pos.moves(as_string=True))
        pos.move_piece(63,0)
    duration=time()-start
    NPS = int(round(total/duration,0)) 
    print("\n"+f"{NPS=:<15_}{total=:<15_}{duration=:.1f}sec {64*rounds/duration:_},  ns per position: {duration/(rounds*64)*1_000_000:.4f}")

def iter3():
    pass

if __name__ =="__main__":
    iter2()
