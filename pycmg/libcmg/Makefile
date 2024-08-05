SHELL       := /bin/bash
CXXFLAGS    := -O2  -fPIC  -march=native  -I. -Wall
CXX         := g++

all: libcmg

libsurge: 
	$(CXX) $(CXXFLAGS) libsurge.cpp -c  -o libsurge.o
	ar rcs libsurge.a libsurge.o
	
libcmg: libsurge
	$(CXX) $(CXXFLAGS) libcmg.cpp -c  -o libcmg.o
	ar rcs libcmg.a libcmg.o
	
deploy:
	cp *.a ..

clean: 
	rm -rf *.so *.o *.a a.out