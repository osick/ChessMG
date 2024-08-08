# cython: language_level=3
# cython: c_string_type=unicode, c_string_encoding=utf8
# distutils: language=c++

from libcpp cimport bool
from libcpp.string cimport string
from libcpp.vector cimport vector
from libc.stdint cimport int64_t, uint64_t, uint8_t
from enum import Enum

class Color(Enum):
    WHITE = 0
    BLACK = 0

cdef extern from "libcmg.h" namespace "cmg":
    cdef cppclass CMGPosition:
        CMGPosition()
        CMGPosition(string fen) except +
        string fen()
        void set_fen(string fen) #TODO
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
    def __init__(self,str fen): self._pos = new CMGPosition(fen)
    def fen(self): return self._pos.fen()
    def print(self): return self._pos.print()
    def turn(self): return self._pos.turn()
    def move_piece(self,int _from, int to):  self._pos.move_piece(_from, to)
    def perft(self,int depth): return self._pos.perft(depth)
    def is_legal(self): return self._pos.is_legal()
    def state(self, color): return self._pos.state(color)
    def moves(self, as_string=False, color=None):
        if color is None: color = self._pos.turn() 
        moves=self._pos.moves(color)
        return [f"{sqstr(moves[m])}-{sqstr(moves[m+1])}" for m in range(0,len(moves)-1,3)] if as_string else moves

    def set_fen(self, string fen): #TODO
        self._pos.set_fen(fen) #TODO

def moves(str fen, bool w):
    position = ChessMoveGenerator(fen) 
    return position.moves(color=(0 if w==True else 1))
    
def perft(fen,depth):
    position = ChessMoveGenerator(fen)
    return position.perft(depth)
    