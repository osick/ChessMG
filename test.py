from timeit import timeit
from time import time,sleep
import json
import sys
import os

from libpycmg import moves, Pos, perft

data =[
    "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R b KQkq - 0 1",
    "1Bn5/1n6/2q5/8/8/8/8/1K5k w - - 0 1",
    "r3kbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQK2R w KQkq - 0 1",
    "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
    "8/k1P5/8/1K6/8/8/8/8 w - - 0 1"
]

def test_average(data):
    rounds=100_000
    for i,fen in enumerate(data):
        w=(fen.split(" ")[1])
        testmoves=moves(fen,w=="w")
        movenumber=len(testmoves)//3
        result = timeit(stmt=f"p.get_{w}_moves()", setup=f'from libpycmg import Pos; p=Pos("{fen}")', number=rounds)
        print(f"SUCCESS: NPS={rounds*movenumber//result:_} ({rounds*movenumber:_} moves) {fen=}, turn={w}")

def test_correctness():
    with open("testdata.json","r") as fh: testdata=json.load(fh)
    sleep(0.1)
    for pos in testdata:
        nodes = perft(pos["fen"], pos["depth"])
        print(f"{'  ERROR: ' if nodes != pos['nodes'] else 'SUCCESS: '}depth={pos['depth']:<2} MUST_nodes={pos['nodes']:<10} IS_nodes={nodes:<10} remark:{pos['remark'][:17]+('...' if len(pos['remark'])>15 else''):<21} {pos['fen']=:<15}")
        
def test_perft(data,depth):
    allnodes=0
    for fen in data:
        start=time();  nodes = perft(fen,depth); duration=time()-start
        if nodes >0:
            print(f"{'SUCCESS: '}NPS={int(round(nodes/duration,0)):<15_}{nodes=:<15_}{duration=:<6.1f}{fen=}")
        allnodes+=nodes
    return allnodes

def perft_start_fen(depth):
    fen="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    start=time();  nodes = perft(fen,depth); duration=time()-start
    print(f"{'SUCCESS: '}NPS={int(round(nodes/duration,0)):<15_}{nodes=:<15_}{duration=:<6.1f}")

if __name__ =="__main__":
    box="▉"; print()
    print(box*140)
    testnumber = input("which test?")
    testnumber = 1 if not testnumber.isdigit() else int(testnumber)

    if testnumber==1:
        print("\nperft_start_fen...\n")
        perft_start_fen(7)
    if testnumber==2:
        print("\ntest_correctness...\n")
        test_correctness()
    if testnumber==3:
        print("\ntest_average...\n")
        test_average(data=data)
    if testnumber==4:
        print("\ntest_performane...\n")
        with open("testdata.json","r") as fh: testdata=json.load(fh)
        alldata =[d['fen'] for d in testdata] + data
        allnodes=0
        alltext=""
        start_total_time=time()
        for depth in range (4):
            nodes=test_perft(data=alldata, depth=depth+1)
            allnodes+=nodes
            alltext+=f"Depth {depth+1}: {nodes:_} nodes"+"\n"
        total_time=time() - start_total_time
        NPS=f"{int(round(allnodes/total_time)):,}"
        print(f"{alltext}"+"\n"+f"{NPS} NPS, {allnodes:,} Nodes, {total_time:.1f} Sec.","\n")

    print("\n"+box*140+"\n")

