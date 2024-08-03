# cython: language_level=3
# cython: c_string_type=unicode, c_string_encoding=utf8
# distutils: language=c++

from libcpp cimport bool
from libcpp.string cimport string
from libcpp.vector cimport vector
import numpy as np
from libc.stdint cimport int64_t, uint64_t

cdef extern from "libcmg.h" namespace "cmg":

    cdef cppclass CPosition:
        CPosition()
        CPosition(string fen) except +
        string fen()
        void set_fen(string fen)
        void print()
        int turn()
        bool is_legal()
        vector[int] get_w_moves()           
        vector[int] get_b_moves()           
        vector[uint64_t] all_pieces()           
        void move_piece(int _from, int to)
        int64_t perft_w(int depth)
        int64_t perft_b(int depth)   
    cdef string sqstr(int idx)


cdef class Pos:
    cdef CPosition* _pos

    def __init__(self,str fen): 
        self._pos = new CPosition(fen)

    def fen(self): 
        return self._pos.fen()

    def set_fen(self, string fen): 
        self._pos.set_fen(fen)

    def print(self): 
        return self._pos.print()

    def get_w_moves(self,as_string=False): 
        moves=self._pos.get_w_moves()
        if as_string:
            sq_moves=[]
            for m in range(0,len(moves)-1,3):
                sq_moves.append(f"{sqstr(moves[m])}-{sqstr(moves[m+1])}")
            return sq_moves
        else:
            return self._pos.get_b_moves()

    def get_b_moves(self, as_string=False): 
        moves=self._pos.get_b_moves()
        if as_string:
            sq_moves=[]
            for m in range(0,len(moves)-1,3):
                sq_moves.append(f"{sqstr(moves[m])}-{sqstr(moves[m+1])}")
            return sq_moves
        else:
            return self._pos.get_b_moves()
    
    def turn(self): 
        return self._pos.turn()
    
    def all_pieces(self):
        return self._pos.all_pieces()

    def move_piece(self,int _from, int to): 
        self._pos.move_piece(_from, to)

    def perft_w(self,int depth):
        cdef int64_t nodes
        nodes = self._pos.perft_w(depth)
        return nodes

    def is_legal(self):
        return self._pos.is_legal()

    def perft_b(self,int depth):
        cdef int64_t nodes
        nodes = self._pos.perft_b(depth)
        return nodes
        
def moves(str fen, bool w):
    position = Pos(fen) 
    if w: return position.get_w_moves()
    else: return position.get_b_moves()

def perft(fen,depth):
    position = Pos(fen)
    return position.perft_w(depth) if position.turn()==0 else position.perft_b(depth)