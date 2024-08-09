from chessmg import ChessMoveGenerator, PC, SQ
from time import time
import json
Pattern = ["K","k","R"]
epsq = 64; white_turn = True; castling = ""

states = []

input ={
    "raw":[(),(),()],
    "epsq":epsq, 
    "turn":white_turn, 
    "castling":castling}

start=time()
total_moves=0
for i0, sqK in enumerate(SQ):
    input["raw"][0] = (PC["K"].value,sqK.value)
    idx=i0
    for i1,sqk in enumerate(SQ):
        if sqk.value!=sqK.value:
            input["raw"][1] = (PC["k"].value,sqk.value)
            for i2, sqR in enumerate(SQ):
                if sqR.value!=sqk.value and sqR.value!= sqK.value:
                    input["raw"][2] = (PC["R"].value,sqR.value)
                    p = ChessMoveGenerator(input)
                    states.append([i0*64**2+i1*64+i2,p.state(0)])
                    total_moves += p.perft(2)
end=time()

print(end-start, len(states), total_moves, f"{int(round(total_moves/(end-start),0)):_}")

#stat_json={"states":states}
print(len([x for x in states if x[1]!=0]))
#with open("stats.txt","w") as fh: fh.write(json.dumps(stat_json))