SHELL := /bin/bash
CXXFLAGS     := -O2 -fPIC -std=c++20 -march=native -I. 
CXX          := g++-13
SRC 		 := libcmg/libsurge.cpp libcmg/libcmg.cpp
OBJS 		 := $(SRC:.cpp=.o)
TARGET 		 := lib/libcmg.so

LD_LIBRARY_PATH := .

.PHONY: all

all: clean pycmg

libsurge:
	$(CXX) $(CXXFLAGS) libcmg/libsurge.cpp -c  
	$(CXX) -shared -Wl,--no-undefined -o libsurge.so libsurge.o

libcmg: libsurge
	$(CXX) $(CXXFLAGS) libcmg/libcmg.cpp -c  
	$(CXX) -shared -Wl,--no-undefined -L. -lsurge -o libcmg.so libcmg.o 

pycmg: libcmg
	python3 setup.py build_ext --inplace
	mv pycmg.cpython-311-x86_64-linux-gnu.so pycmg.so
	rm *.o
	rm -rf build

clean:
	rm -rf *.so *.o
	rm -rf build 
	rm -rf pycmg.egg-info
	rm -rf libpycmg.cpp