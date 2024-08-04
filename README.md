# PYCMG

**pycmg** is a python library which generates chess moves in a given FEN position quite fast.
Technically it uses the very fast Chess Move Generator libary "surge" (see https://github.com/nkarve/surge) written in C++, which is embedded in the python module via cython. It is quite fast and can reach more than 200.000.000 NPS (nodes per second) in the perft test. 
For more details see below.   

## Start it!

### Prerequisites

The installation requires the following components
  - The cython libary (https://github.com/cython/cython). It can simply been installed by `pip install cython`
  - The Python-development packages including the python header **Python.h** (*python-dev* on Debian, *python3-devel* on OpenSuSe, for more see https://docs.python.org/3/c-api/index.html)
- A quite decent version of the GCC C++ compiler (https://gcc.gnu.org) which supports std=c++20 and higher. This is the standard comiling environment on main Linux/Unix Platforms and also available for Windows, for more see https://gcc.gnu.org. 
  
### Installation
get it from github and install it from the source directory via pip

```bash
> git clone https://github.com/osick/pycmg.git
> cd pycmg
> pip install .
```

Now a first test:  

```bash
> cd tests
> python test_perft_start_fen.py 
```

The test looks for correct comuptation of nodes and the result should look like

```
 perft results for chess starting position up to depth 7
=========================================================
passed: result=20              | perft(1)=20              | 586,616 NPS      | 0.0 seconds
passed: result=400             | perft(2)=400             | 30,504,029 NPS   | 0.0 seconds
passed: result=8,902           | perft(3)=8,902           | 111,789,504 NPS  | 0.0 seconds
passed: result=197,281         | perft(4)=197,281         | 130,308,108 NPS  | 0.0 seconds
passed: result=4,865,609       | perft(5)=4,865,609       | 156,898,926 NPS  | 0.0 seconds
passed: result=119,060,324     | perft(6)=119,060,324     | 201,272,989 NPS  | 0.6 seconds
passed: result=3,195,901,860   | perft(7)=3,195,901,860   | 228,546,291 NPS  | 14.0 seconds

TEST PASSED

```

### Simple usage of pycmg

It all starts with the **Pos** class in the module pycmg. If you want to get the white moves in the starting position 
```python
  from pycmg import Pos
  position = Pos("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
  result = position.get_w_moves(as_string=True)
```

and as a result you get the possible 20 moves as a list 
```python

result = ['b1-a3', 'b1-c3', 'g1-f3', 'g1-h3', 'a2-a3', 'b2-b3', 'c2-c3', 'd2-d3', 'e2-e3', 'f2-f3', 
 'g2-g3', 'h2-h3', 'a2-a4', 'b2-b4', 'c2-c4', 'd2-d4', 'e2-e4', 'f2-f4', 'g2-g4', 'h2-h4']

```

or if you want it as an integer list (represented by the numbering of the squares a1=0, b1=1, ... h8=63)

```python
  result = position.get_w_moves(as_string=False)
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
### perft
You can also make a perft test (see https://www.chessprogramming.org/Perft_Results)

```python

nodes = perft(fen="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",7)

```

It gives the correct number `Perft(7) = nodes = 3_195_901_860`  and takes about 15 seconds (** more than 210.000.000 NPS**). Not the best NPS value, but quite nice for python usage...  


## Next steps

## Acknowledgements

This project uses code from the following open-source projects:

- "surge" project (https://github.com/nkarve/surge) - Licensed under the MIT License




