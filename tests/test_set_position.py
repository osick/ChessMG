from chessmg import ChessMoveGenerator
from time import time
import sys

def test_inp(depth=3):
    inp = {"position":[(13,2), (5,18) , (4,40), (12,53)], "turn":True, "epsq":64, "castling":""}
    c_inp = ChessMoveGenerator(inp)
    inp_total=0
    for i in range(1,depth+1):
        c_inp_result =  c_inp.perft(i)
        inp_total+=c_inp_result
    return inp_total

def test_fen(depth=3):
    c_fen = ChessMoveGenerator("8/5q2/Q7/8/8/2K5/8/2k5 w - - 0 1")
    fen_total=0
    for i in range(1,depth+1):
        c_fen_result =  c_fen.perft(i)
        fen_total+=c_fen_result
    return fen_total

def test_correctness(depth=3,verbose=False):
    inp_nodes , fen_nodes = 0 , 0

    start = time(); 
    inp_nodes=test_inp(depth); 
    t=time()-start; 
    if verbose: print(f"inp: Time:{t:.2f}, NPS={int(round(inp_nodes/t,0)):_}, {inp_nodes=}")

    start = time(); 
    fen_nodes=test_fen(depth); 
    t=time()-start; 
    if verbose: print(f"fen: Time:{t:.2f}, NPS={int(round(fen_nodes/t,0)):_}, {fen_nodes=}")
    
    return inp_nodes, fen_nodes

if __name__ =="__main__":
    verbose = (len(sys.argv)>=2 and sys.argv[1]=="verbose")
    print("\nTest Case ",__file__,sep="")
    depth = 6 if len(sys.argv)<2 else (6 if (not sys.argv[1].isdigit()) else int(sys.argv[1]))
    inp_res, fen_res = test_correctness(depth, verbose)
    success = (inp_res == fen_res)

    {print ("TEST PASSED") and exit(0)} if success else {print ("TEST FAILED") and exit(1)}