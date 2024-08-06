from time import time
import json
from datetime import datetime
from pycmg import perft

def test_perft(data,depth):
    allnodes=0
    text=""
    for fen in data:
        start=time();  nodes = perft(fen,depth); duration=time()-start
        if nodes >0:
            res_text=f"{'SUCCESS: '}NPS={int(round(nodes/duration,0)):<15,}{nodes=:<15,}{duration=:<6.1f}{fen=}"
            text+=res_text+"\n"
            print(res_text)
        allnodes+=nodes
    return allnodes, text

if __name__ =="__main__":
        print("\ntest_performance...\n")
        with open("testdata.json","r") as fh: testdata=json.load(fh)
        alldata =[d['fen'] for d in testdata]
        allnodes=0
        alltext=""
        start_total_time=time()
        for depth in range (5):
            nodes , text =test_perft(data=alldata, depth=depth+1)
            allnodes+=nodes
            alltext += text+f"Depth {depth+1}: {nodes:,} nodes"+"\n"
        total_time=time() - start_total_time
        NPS=f"{int(round(allnodes/total_time)):,}"
        alltext += "\nTOTAL RESULT\n" + ("="*50) + "\n\n" + f"{NPS} NPS, {allnodes:,} Nodes, {total_time:.1f} Sec."+"\n"
        print(f"{alltext}")


        now = datetime.now()
        dt_string = ("-"*20)+now.strftime("%d/%m/%Y %H:%M:%S")+("-"*20)
        
        with open("test_perft.result","a") as fh:
             fh.write(dt_string+"\n"+alltext+"\n"+dt_string+"\n\n")
