# cython: language_level=3
# cython: c_string_type=unicode, c_string_encoding=utf8
# distutils: language=c++

import sys
from libcpp cimport bool
from libcpp.string cimport string
from libcpp.vector cimport vector
from libc.stdint cimport int64_t, uint64_t, uint8_t
from enum import Enum, auto

from libcpp.pair cimport pair as cpair
ctypedef cpair[int, int] ipair

class COLOR(Enum):
    WHITE = 0
    BLACK = 1

class PC(Enum):
    P=0; N=1; B=2; R=3; Q=4; K=5; p=8; n=9; b=10; r=11; q=12; k=13
    NO_PIECE=14

class SQ(Enum): 
    a1=0; b1=auto(); c1=auto(); d1=auto(); e1=auto(); f1=auto(); g1=auto(); h1=auto()
    a2=auto(); b2=auto(); c2=auto(); d2=auto(); e2=auto(); f2=auto(); g2=auto(); h2=auto()
    a3=auto(); b3=auto(); c3=auto(); d3=auto(); e3=auto(); f3=auto(); g3=auto(); h3=auto()
    a4=auto(); b4=auto(); c4=auto(); d4=auto(); e4=auto(); f4=auto(); g4=auto(); h4=auto()
    a5=auto(); b5=auto(); c5=auto(); d5=auto(); e5=auto(); f5=auto(); g5=auto(); h5=auto()
    a6=auto(); b6=auto(); c6=auto(); d6=auto(); e6=auto(); f6=auto(); g6=auto(); h6=auto()
    a7=auto(); b7=auto(); c7=auto(); d7=auto(); e7=auto(); f7=auto(); g7=auto(); h7=auto()
    a8=auto(); b8=auto(); c8=auto(); d8=auto(); e8=auto(); f8=auto(); g8=auto(); h8=auto()
    NO_SQUARE=auto()

cdef extern from "libcmg.h" namespace "cmg":
    cdef cppclass CMGPosition:
        CMGPosition() except +
        CMGPosition(string fen) except +
        CMGPosition(vector[ipair] piecelist, bool turn, int epsq,  string castling) except +
        string fen()
        void set_fen(string fen)
        void print()
        int turn()
        bool is_legal()
        uint8_t state(int c)
        vector[int] moves(int color)              
        int64_t perft(int depth)        
        void move_piece(int _from, int _to)
    cdef string sqstr(int idx)

cdef class ChessMoveGenerator:
    cdef CMGPosition* _pos
    
    def __init__(self, input=None):
        if input is None:
            self._pos = new CMGPosition()
        elif type(input) is str:
            # input is FEN string
            self._pos = new CMGPosition(input)
        elif type(input) is dict:
            # eg input ={"raw":[(1,1),(2,63),...], "turn":bool, eqsq:1, castling:"KQkq"}
            # or 
            # eg input ={"position":[("k","b1"),("K","b8"),...], "turn":bool, eqsq:1, castling:"KQkq"}
            pos = []
            turn = input.get("turn",True)
            epsq = int(input.get("epsq",64))
            castling = str(input.get("castling",""))
            if  "raw" in input:         pos = input["raw"]
            elif "position" in input:   pos = [( PC(it[0]).value , SQ(it[1]).value ) for it in input["position"]]
            self._pos = new CMGPosition(pos, turn, epsq,  castling)

    def set_fen(self,fen):
        self._pos.set_fen(fen)

    def __dealloc__(self):
        del self._pos

    def fen(self): 
        return self._pos.fen()
    
    def print(self): 
        return self._pos.print()
    
    def turn(self): 
        return self._pos.turn()
    
    def move_piece(self,int _from, int _to):  
        self._pos.move_piece(_from, _to)
    
    def perft(self,int depth): 
        return self._pos.perft(depth)
    
    def is_legal(self): 
        return self._pos.is_legal()
    
    def state(self, color): 
        return self._pos.state(color)
    
    def moves(self, as_string=False, color=None):
        if color is None: color = self._pos.turn() 
        moves=self._pos.moves(color)
        return [f"{sqstr(moves[m])}-{sqstr(moves[m+1])}" for m in range(0,len(moves)-1,3)] if as_string else moves

def moves(str fen, bool w):
    position = ChessMoveGenerator(fen) 
    return position.moves(color=(0 if w==True else 1))
    
def perft(fen,depth):
    position = ChessMoveGenerator(fen)
    return position.perft(depth)
    