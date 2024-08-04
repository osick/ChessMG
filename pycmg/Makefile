SHELL := /bin/bash
CXXFLAGS     := -O2 -fPIC -std=c++20 -march=native -I. 
CXX          := g++-13

LD_LIBRARY_PATH := .

.PHONY: all

all: clean libcmg

libsurge:
	echo "nothing to to"
	#$(CXX) $(CXXFLAGS) libcmg/libsurge.cpp -c  
	#$(CXX) -shared -Wl,--no-undefined -o libsurge.so libsurge.o

libcmg: libsurge
	echo "nothing to to"
	#$(CXX) $(CXXFLAGS) libcmg/libcmg.cpp -c  
	#$(CXX) -shared -Wl,--no-undefined -L. -lsurge -o libcmg.so libcmg.o 

clean:
	rm -rf *.so *.o *.a a.out
	rm -f libpycmg.cpp 
	pushd libcmg && make clean

