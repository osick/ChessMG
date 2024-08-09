import sys
import os
from time import time
from datetime import datetime
from chessmg import perft

# from https://www.chessprogramming.org/Perft_Results
perft_result=[
    1,    #depth 0
    20,    #depth 1
    400,    #depth 2
    8902,    #depth 3
    197281,   #depth 4
    4865609,   #depth 5
    119060324,  #depth 6
    3195901860,  #depth 7
    84998978956,  #depth 8
    2439530234167, #depth 9
    ]  


def perft_time(fen,depth,verbose=False):

    start=time();  
    nodes = perft(fen,depth); 
    duration=time()-start
    
    result= ("error :" if nodes != perft_result[depth] else "passed:")
    result_txt=f"{result} result={nodes:<15,} | perft({depth})={perft_result[depth]:<15,} | {f'{int(round(nodes/duration,0)):,}'+' NPS':16} | {duration:.1f} seconds"
    if verbose: print(result_txt)
    return (nodes == perft_result[depth]),result_txt

if __name__ =="__main__":
    print("\nTest Case ",__file__,sep="")
    maxdepth=6
    if len(sys.argv)>=2:
        if sys.argv[1].isdigit(): maxdepth=max(1,int(sys.argv[1]))
        if maxdepth>=len(perft_result):
            print(f"perft results only up to depth {len(perft_result)-1}. Abort!")
            exit()
    verbose = (len(sys.argv)>=3 and sys.argv[2]=="verbose")
    
    fen="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"

    title="perft results for chess starting position up to depth "+str(maxdepth)
    alltext="\n"+title+"\n"+"="*(len(title)+2)+"\n"
    if verbose: print(alltext)
    total = True
    for depth in range(1,maxdepth+1):
        _total, text = perft_time(fen=fen , depth=depth,verbose=verbose)
        total = total & _total
        alltext+= text+"\n"
    
    now = datetime.now()
    dt_string = ("-"*20)+now.strftime("%d/%m/%Y %H:%M:%S")+("-"*20)

    with open(os.path.join(os.path.dirname(os.path.realpath(__file__)),"test_perft_start_fen.result"),"a") as fh:
        fh.write("\n"+dt_string+"\n\n"+alltext+"\n\n"+dt_string+"\n\n")

    if total==True: print ("TEST PASSED"); exit(0)
    else: print ("TEST FAILED"); exit(1)
 
        
