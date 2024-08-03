SHELL := /bin/bash
CXXFLAGS     := -O2 -fPIC -std=c++20 -march=native -I./include 
CXX          := g++-13
#SRC 		 := src/types.cpp src/tables.cpp src/position.cpp src/libcmg.cpp
SRC 		 := src/libsurge.cpp src/libcmg.cpp
OBJS 		 := $(SRC:.cpp=.o)
TARGET 		 := lib/libcmg.so

LD_LIBRARY_PATH := .

.PHONY: all

all: clean libpycmg install clean

libsurge:
	$(CXX) $(CXXFLAGS) src/libsurge.cpp -c  
	#$(CXX) -shared -Wl,--no-undefined -o lib/libsurge.so libsurge.o
	$(CXX) -shared -Wl,--no-undefined -o libsurge.so libsurge.o

libcmg: libsurge
	$(CXX) $(CXXFLAGS) src/libcmg.cpp -c  
	#$(CXX) -shared -Wl,--no-undefined -L./lib -lsurge -o lib/libcmg.so libcmg.o 
	$(CXX) -shared -Wl,--no-undefined -L. -lsurge -o libcmg.so libcmg.o 

libpycmg: libcmg
	python3 setup.py build_ext --inplace
	mv libpycmg.cpython-311-x86_64-linux-gnu.so libpycmg.so
	rm *.o
	rm -rf build

test: 
	export LD_LIBRARY_PATH=${LD_LIBRARY_PATH} && python3 test.py

env:
	python3 -c "import sys; print('; '.join(sys.path))"

install:
	python3 setup.py install

html:
	cythonize -a -i src/libpycmg.pyx
	rm -rf  src/libpycmg.cpp

clean:
	rm -rf lib/*.so src/*.so src/*.o *.so *.o
	rm -rf build
	rm -rf  src/libpycmg.cpp