from chessmg import ChessMoveGenerator, PC, SQ
from time import time
import json
import os


def iter1():
    #       "depth":1,
    #       "nodes":19,
    #       "fen":"r1bqkbnr/pppppppp/n7/8/8/P7/1PPPPPPP/RNBQKBNR w KQkq - 2 2",
    #       "remark":""
    with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), ".." , "tests" , "testdata.json"),"r") as fh: 
        testdata=json.load(fh)

    pos = ChessMoveGenerator()
    start=time()
    nodes_total= 0
    for i in range(2):
        for item in testdata:
            if item["depth"]==1:
                pos.set_fen(item["fen"])
                #pos.print()
                nodes = len(pos.moves())//3
                nodes_total+=nodes
                print(f"{i:<5} {item['nodes'] = :<20} {nodes = :<20} {item['fen']}")
    duration=time()-start
    NPS = int(round(nodes_total/duration,0)) 
    print(f"{NPS=:<20_}{duration:.1f}")

def iter2():
    fen="8/5q2/Q7/8/8/8/8/K1k5 w - - 0 1"
    input = {"raw":[(13,2), (5,0) , (4,40), (12,53)], "turn":True, "epsq":64, "castling":""} #
    pos = ChessMoveGenerator(fen)
    total= len(pos.moves())//3
    start=time()
    rounds=10000
    for k in range(rounds):
        this = 0
        for i in range(0,63):
            next=i+1
            if next not in [2,40,53]:
                pos.move_piece(this,next)
                this=next
                mvs= pos.moves()
                nodes = len(mvs)//3
                total+=nodes
                #pos.print()
                #print(f"K{SQ(next).name}", pos.is_legal(), pos.turn(), pos.state(0), pos.state(1), pos.moves(as_string=True))
                #print(f"{i:<5} {next=} {nodes = :<20}")
                #print("-"*140+"\n")
        pos.move_piece(63,0)
    duration=time()-start
    NPS = int(round(total/duration,0)) 
    print(f"{NPS=:<15_}{total=:<15_}{duration=:.1f}sec {64*rounds/duration:_}")

if __name__ =="__main__":
    iter2()
