SHELL       := /bin/bash

all: pipeine
	

install:
	pip install .

uninstall:
	pip uninstall -y pycmg

clean:
	rm -rf build
	rm -rf pycmg.egg-info
	rm -rf *.so *.o *.a a.out
	pushd pycmg && make clean

example:
	pushd examples && python3 simple.py

test:
	pushd tests && python3 test_perft_start_fen.py 6
	pushd tests && python3 test_correctness.py

pipeline: clean uninstall install test
