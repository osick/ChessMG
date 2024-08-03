# PYCMG

**pycmg** is a python library which generates chess moves in a given FEN position quite fast.
Technically it uses the very fast Chess Move Generator libary "surge" (see https://github.com/nkarve/surge) written in C++, which is embedded in the python module via cython.

## Installation
The installation requires the following components
- The cython libary (https://github.com/cython/cython)
- A quite decent version of the GCC C++ compiler () which supports std=c++20 and higher

Download it, then compile
```
git clone https://github.com/osick/pycmg.git
make libpycmg
```

### First Try

Make a first test:  `python test.py `. The test result should look like

```
test_correctness...

SUCCESS: depth=1     MUST_nodes=8               IS_nodes=8          remark: black's turn and check         pos['fen']=r6r/1b2k1bq/8/8/7B/8/8/R3K2R b - - 0 1
SUCCESS: depth=1     MUST_nodes=19              IS_nodes=19         remark:                                pos['fen']=r1bqkbnr/pppppppp/n7/8/8/P7/1PPPPPPP/RNBQKBNR w KQkq - 2 2
  ERROR: depth=1     MUST_nodes=8               IS_nodes=7          remark: en passant at d3               pos['fen']=8/8/8/2k5/2pP4/8/B7/4K3 b - d3 0 3
SUCCESS: depth=1     MUST_nodes=8               IS_nodes=8          remark: black's turn and check = #1    pos['fen']=r6r/1b2k1bq/8/8/7B/8/8/R3K2R b - - 0 1
SUCCESS: depth=1     MUST_nodes=5               IS_nodes=5          remark:                                pos['fen']=r3k2r/p1pp1pb1/bn2Qnp1/2qPN3/1p2P3/2N5/PPPBBPPP/R3K2R b KQkq - 3 2
SUCCESS: depth=1     MUST_nodes=44              IS_nodes=44         remark:                                pos['fen']=2kr3r/p1ppqpb1/bn2Qnp1/3PN3/1p2P3/2N5/PPPBBPPP/R3K2R b KQ - 3 2
SUCCESS: depth=1     MUST_nodes=39              IS_nodes=39         remark:                                pos['fen']=rnb2k1r/pp1Pbppp/2p5/q7/2B5/8/PPPQNnPP/RNB1K2R w KQ - 3 9
SUCCESS: depth=1     MUST_nodes=9               IS_nodes=9          remark:                                pos['fen']=2r5/3pk3/8/2P5/8/2K5/8/8 w - - 5 4
SUCCESS: depth=3     MUST_nodes=62379           IS_nodes=62379      remark:                                pos['fen']=rnbq1k1r/pp1Pbppp/2p5/8/2B5/8/PPP1NnPP/RNBQK2R w KQ - 1 8
SUCCESS: depth=3     MUST_nodes=89890           IS_nodes=89890      remark:                                pos['fen']=r4rk1/1pp1qppp/p1np1n2/2b1p1B1/2B1P1b1/P1NP1N2/1PP1QPPP/R4RK1 w - - 0 10
SUCCESS: depth=6     MUST_nodes=1134888         IS_nodes=1134888    remark: en passant pinning next ply    pos['fen']=3k4/3p4/8/K1P4r/8/8/8/8 b - - 0 1
SUCCESS: depth=6     MUST_nodes=1015133         IS_nodes=1015133    remark: en passant pinning next ply    pos['fen']=8/8/4k3/8/2p5/8/B2P2K1/8 w - - 0 1
  ERROR: depth=6     MUST_nodes=1440467         IS_nodes=1400374    remark: en passant at d3               pos['fen']=8/8/1k6/2b5/2pP4/8/5K2/8 b - d3 0 1
SUCCESS: depth=6     MUST_nodes=661072          IS_nodes=661072     remark:                                pos['fen']=5k2/8/8/8/8/8/8/4K2R w K - 0 1
SUCCESS: depth=6     MUST_nodes=803711          IS_nodes=803711     remark:                                pos['fen']=3k4/8/8/8/8/8/8/R3K3 w Q - 0 1
SUCCESS: depth=4     MUST_nodes=1274206         IS_nodes=1274206    remark:                                pos['fen']=r3k2r/1b4bq/8/8/8/8/7B/R3K2R w KQkq - 0 1
SUCCESS: depth=4     MUST_nodes=1720476         IS_nodes=1720476    remark:                                pos['fen']=r3k2r/8/3Q4/8/8/5q2/8/R3K2R b KQkq - 0 1
SUCCESS: depth=6     MUST_nodes=3821001         IS_nodes=3821001    remark:                                pos['fen']=2K2r2/4P3/8/8/8/8/8/3k4 w - - 0 1
SUCCESS: depth=5     MUST_nodes=1004658         IS_nodes=1004658    remark:                                pos['fen']=8/8/1P2K3/8/2n5/1q6/8/5k2 b - - 0 1
SUCCESS: depth=6     MUST_nodes=217342          IS_nodes=217342     remark:                                pos['fen']=4k3/1P6/8/8/8/8/K7/8 w - - 0 1
SUCCESS: depth=6     MUST_nodes=92683           IS_nodes=92683      remark:                                pos['fen']=8/P1k5/K7/8/8/8/8/8 w - - 0 1
SUCCESS: depth=6     MUST_nodes=2217            IS_nodes=2217       remark:                                pos['fen']=K1k5/8/P7/8/8/8/8/8 w - - 0 1
SUCCESS: depth=7     MUST_nodes=567584          IS_nodes=567584     remark:                                pos['fen']=8/k1P5/8/1K6/8/8/8/8 w - - 0 1
SUCCESS: depth=4     MUST_nodes=23527           IS_nodes=23527      remark:                                pos['fen']=8/8/2k5/5q2/5n2/8/5K2/8 b - - 0 1
SUCCESS: depth=4     MUST_nodes=0               IS_nodes=0          remark: kings in direct contact        pos['fen']=8/8/8/8/3k4/4K3/8/8 w - - 0 1
SUCCESS: depth=4     MUST_nodes=0               IS_nodes=0          remark: wP on 1st rank                 pos['fen']=8/8/8/8/3k4/8/4K3/6P1 b - - 0 1
SUCCESS: depth=4     MUST_nodes=0               IS_nodes=0          remark: wP on 8th rank                 pos['fen']=6P1/8/8/8/3k4/8/4K3/8 b - - 0 1
SUCCESS: depth=1     MUST_nodes=6               IS_nodes=6          remark: check by white                 pos['fen']=8/4k3/8/8/7B/8/8/4K3 b - - 0 1

```
**Note**: The two "ERROR" messages indicate a bug with en passant in the fen description.... will be fixed....

### Simple usage

It all starts with the **Pos** class in the module pycmg. If you want to get the white moves in the starting position 
'''Python
from libpycmg import Pos
position = Pos("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
print(position.get_w_moves(as_string=True))
'''

and you get the list of the possible 20 moves 
'''
['b1-a3', 'b1-c3', 'g1-f3', 'g1-h3', 'a2-a3', 'b2-b3', 'c2-c3', 'd2-d3', 'e2-e3', 'f2-f3', 'g2-g3', 'h2-h3', 'a2-a4', 'b2-b4', 'c2-c4', 'd2-d4', 'e2-e4', 'f2-f4', 'g2-g4', 'h2-h4']
'''


## Next steps

## Acknowledgements

This project uses code from the following open-source projects:

- "surge" project (https://github.com/nkarve/surge) - Licensed under the MIT License




