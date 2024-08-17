SHELL                     := /bin/bash
CXXFLAGS                  := -O2  -fPIC     -march=native  -I. -Wall 
CXX                       := g++
CXX_MAIN_FLAGS            := -O2 -std=c++20 -march=native -I. -Wall 
CXX_MULTITHREADING_FLAGS  := -pthread



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
	rm -rf tests/exec_*

buildtest:
	$(CXX) $(CXX_MAIN_FLAGS) tests/test_libsurge.cpp  -L. -l:libsurge.a              -o tests/exec_test_libsurge
	$(CXX) $(CXX_MAIN_FLAGS) tests/test_libcmg.cpp    -L. -l:libcmg.a -l:libsurge.a  -o tests/exec_test_libcmg
	$(CXX) $(CXX_MAIN_FLAGS) $(CXX_MULTITHREADING_FLAGS)   tests/test_libsurge_multithreading.cpp  -L. -l:libcmg.a -l:libsurge.a 	-o tests/exec_test_libsurge_multithreading

test: buildtest
	./tests/exec_test_libsurge
	./tests/exec_test_libcmg
	./tests/exec_test_libsurge_multithreading 7

iter: libcmg
	$(CXX) $(CXX_MAIN_FLAGS) $(CXX_MULTITHREADING_FLAGS) tests/test_iterator.cpp  	-L. -l:libcmg.a -l:libsurge.a 	-o tests/exec_test_iterator
	./tests/exec_test_iterator
