SHELL       := /bin/bash
CXXFLAGS    := -O2  -fPIC  -march=native  -I. -Wall
CXX         := g++
CXX_MAIN_FLAGS 	:= -O2 -std=c++20 -march=native -I. -Wall

all: libcmg

pipeline: clean libcmg test
	
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
	rm -rf tests/test_libsurge
	rm -rf tests/test_libcmg

buildtest: libcmg
	$(CXX) $(CXX_MAIN_FLAGS)  			tests/test_libsurge.cpp -L. -l:libsurge.a  				-o tests/test_libsurge
	$(CXX) $(CXX_MAIN_FLAGS)  			tests/test_libcmg.cpp   -L. -l:libcmg.a -l:libsurge.a 	-o tests/test_libcmg
	$(CXX) $(CXX_MAIN_FLAGS) -pthread   tests/test_threading.cpp  	-L. -l:libcmg.a -l:libsurge.a 	-o tests/test_threading

test: buildtest
	./tests/test_libsurge
	./tests/test_libcmg
	./tests/test_threading 6
