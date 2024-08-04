import sys
from time import time
from pycmg import perft

# from https://www.chessprogramming.org/Perft_Results
perft_result=[1,20,400,8902,197281, 4865609, 119060324, 3195901860, 84998978956, 2439530234167]


def perft_time(fen,depth):
    start=time();  nodes = perft(fen,depth); duration=time()-start
    result="error :" if nodes != perft_result[depth] else "passed:"
    print(f"{result} result={nodes:<15,} | perft({depth})={nodes:<15,} | {f'{int(round(nodes/duration,0)):,}'+' NPS':16} | {duration:.1f} seconds")
    return (nodes == perft_result[depth])

if __name__ =="__main__":
    maxdepth=7
    if len(sys.argv)>=2:
        if sys.argv[1].isdigit(): maxdepth=max(1,int(sys.argv[1]))
        if maxdepth>=len(perft_result):
            print(f"perft results only up to depth {len(perft_result)-1}. Abort!")
            exit()
    fen="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"

    title="perft results for chess starting position up to depth "+str(maxdepth)
    print("\n "+title+"\n"+"="*(len(title)+2))
    total = True
    for depth in range(1,maxdepth+1):
        _total = perft_time(fen=fen , depth=depth)
        total = total & _total

    if total==True: print ("\nTEST PASSED\n"); exit(0)
    else: print ("\nTEST FAILED\n"); exit(1)

