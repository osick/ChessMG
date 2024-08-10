SHELL       := /bin/bash

PHONY: clean test install uninstall example pipeline

.SILENT: clean test

all: pipeine
	

install:
	pip install .

uninstall:
	pip uninstall -y chessmg

clean:
	rm -rf build
	rm -rf *.egg-info
	rm -rf *.so *.o *.a a.out
	pushd chessmg && make clean

example:
	pushd examples && python3 simple.py

test:
	@python3 tests/test_perft_start_fen.py 7 verbose
	@python3 tests/test_correctness.py 
	@python3 tests/test_set_position.py verbose

pipeline: clean uninstall install test
