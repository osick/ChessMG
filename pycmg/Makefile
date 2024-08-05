SHELL := /bin/bash
CXXFLAGS     := -O2 -fPIC -std=c++20 -march=native -I. 
CXX          := g++-13

LD_LIBRARY_PATH := .

.PHONY: all

all: clean libcmg

libsurge:
	echo "nothing to to"

libcmg: libsurge
	echo "nothing to to"

clean:
	rm -rf *.so *.o *.a a.out
	rm -f libpycmg.cpp 
	pushd libcmg && make clean
