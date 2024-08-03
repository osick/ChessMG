from time import time
import json

from pycmg import perft

def test_perft(data,depth):
    allnodes=0
    for fen in data:
        start=time();  nodes = perft(fen,depth); duration=time()-start
        if nodes >0:
            print(f"{'SUCCESS: '}NPS={int(round(nodes/duration,0)):<15_}{nodes=:<15_}{duration=:<6.1f}{fen=}")
        allnodes+=nodes
    return allnodes

if __name__ =="__main__":
        print("\ntest_performance...\n")
        with open("testdata.json","r") as fh: testdata=json.load(fh)
        alldata =[d['fen'] for d in testdata]
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
