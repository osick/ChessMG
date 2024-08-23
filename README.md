# chessmg

**chessmg** (**Chess** **M**ove **G**enerator) is a python library which generates chess moves in a given FEN position quite fast.

Technically it relies on the very fast Chess Move Generator libary "surge" (https://github.com/nkarve/surge) written in C++, which is embedded via cython. 

**chessmg** is quite fast and single threaded it reaches about 250.000.000 NPS (nodes per second). 
Multithreaded we can reach about 2 Billion moves per second. For more details see the [PERFT](#PERFT) section

## Start it!

### Prerequisites

The installation requires the following components
  - The cython libary (https://github.com/cython/cython). It can simply been installed by `pip install cython`
  - The Python-development packages including the python header **Python.h** (*python-dev* on Debian, *python3-devel* on OpenSuSe, for more see https://docs.python.org/3/c-api/index.html)
- A quite decent version of the GCC C++ compiler (https://gcc.gnu.org) which supports std=c++20 and higher. This is the standard comiling environment on main Linux/Unix Platforms and also available for Windows, for more see https://gcc.gnu.org. 
  
### Installation
get it from github and install it from the source directory via pip

```bash
> git clone https://github.com/osick/chessmg.git
> cd chessmg
> pip install .
```

### PERFT

There is a standardtest for chess move generators, namely the so callled perft (aka performanca test, for more see https://www.chessprogramming.org/Perft_Results ). 
The single threaded mode can be sinmply tested as follows:

```bash
> cd tests
> python test_perft_start_fen.py 
```
The test looks for correct computation of nodes (different move sequences from a given starting position) and the result should look like

```
 perft results for chess starting position up to depth 7
=========================================================

passed: result=20              | perft(1)=20              | 1,061,849 NPS    | 0.0 seconds
passed: result=400             | perft(2)=400             | 44,150,568 NPS   | 0.0 seconds
passed: result=8,902           | perft(3)=8,902           | 196,514,180 NPS  | 0.0 seconds
passed: result=197,281         | perft(4)=197,281         | 220,185,335 NPS  | 0.0 seconds
passed: result=4,865,609       | perft(5)=4,865,609       | 245,139,259 NPS  | 0.0 seconds
passed: result=119,060,324     | perft(6)=119,060,324     | 233,346,570 NPS  | 0.5 seconds
passed: result=3,195,901,860   | perft(7)=3,195,901,860   | 249,988,283 NPS  | 12.8 seconds

TEST PASSED

```

It gives the correct number `Perft(7) = nodes = 3,195,901,860`  and here it takes about 13 seconds (** about 250.000.000 NPS**). 
Not the best NPS value compard to the original surge libraray (which is twice as fast) or other Libs as Gigantua etc.. But it is quite nice for Python.

Applying perft.py (see https://github.com/niklasf/python-chess/blob/master/examples/perft/perft.py) of the very good native python chess library, *Python-chess* we get around 3.500.000 NPS. this is a performance win of around factor 70. The performance of course depends on the underlying hardware. 

As said before there is a protytypical **multithreaded implementation which can reach more than 2 Billion NPS** (only in C++ up to now, but it can simply be extended to python....). 

### Simple usage of chessmg

It all starts with the **ChessMoveGenerator** class in the module chessmg. If you want to get the white moves in the starting position 
```python

  from chessmg import ChessMoveGenerator
  position = ChessMoveGenerator("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
  result = position.moves(as_string=True)

```

and as a result you get the possible 20 moves as a list 
```python

result = ['b1-a3', 'b1-c3', 'g1-f3', 'g1-h3', 'a2-a3', 'b2-b3', 'c2-c3', 'd2-d3', 'e2-e3', 'f2-f3', 
 'g2-g3', 'h2-h3', 'a2-a4', 'b2-b4', 'c2-c4', 'd2-d4', 'e2-e4', 'f2-f4', 'g2-g4', 'h2-h4']

```

or if you want it as an integer list (represented by the numbering of the squares a1=0, b1=1, ... h8=63)

```python

  result = position.moves(as_string=False)
  >>> result = 
  [[57 40  0]
    [57 42  0]
    [62 45  0]
    [62 47  0]
    [48 40  0]
    [49 41  0]
    [50 42  0]
    [51 43  0]
    [52 44  0]
    [53 45  0]
    [54 46  0]
    [55 47  0]
    [48 32  1]
    [49 33  1]
    [50 34  1]
    [51 35  1]
    [52 36  1]
    [53 37  1]
    [54 38  1]
  ]

````

For each move the last entry is the move flag, inhereted from the surge lib. "0" is for ordinary move, "1" is for a double step of a pawn etc. For more see the libsurge.h file.

## Next steps

## Acknowledgements

This project uses code from the following open-source projects:

- "Surge" Library from https://github.com/nkarve/surge - Licensed under the MIT License




