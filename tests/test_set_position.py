from chessmg import ChessMoveGenerator
from time import time
import sys

def test(input, depth,verbose=False):
    start = time(); 
    c_inp = ChessMoveGenerator(input)
    nodes = sum([c_inp.perft(i) for i in range(1,depth+1)])
    final = time()-start; 
    if verbose: print(f"inp: Time:{final:.2f}, NPS={int(round(nodes/final,0)):_}, {nodes=}")
    return nodes

if __name__ =="__main__":
    verbose = (len(sys.argv)>=2 and sys.argv[1]=="verbose")
    result = []
    for input in [
        {"raw":[(13,2), (5,18) , (4,40), (12,53)], "turn":True, "epsq":64, "castling":""},
        "8/5q2/Q7/8/8/2K5/8/2k5 w - - 0 1"
        ]:
        result.append(test(input,6,verbose))

    {print("TEST PASSED") and exit(0)} if (len(set(result))==1) else {print("TEST FAILED") and exit(1)}