// This file incorporates code from the "surge" project (https://github.com/nkarve/surge),
// which is licensed under the MIT License:
//
// MIT License
// 
// Copyright (c) 2020 DiehardTheTryhard
// 
// Permission is hereby granted, free of charge, to any person obtaining a copy
// of this software and associated documentation files (the "Software"), to deal
// in the Software without restriction, including without limitation the rights
// to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
// copies of the Software, and to permit persons to whom the Software is
// furnished to do so, subject to the following conditions:
// 
// The above copyright notice and this permission notice shall be included in all
// copies or substantial portions of the Software.
// 
// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
// IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
// FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
// AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
// LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
// OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
// SOFTWARE.

// see https://github.com/nkarve/surge/blob/master/src/chess_engine.cpp

#include <iostream>
#include <chrono>
#include "libsurge.h"


template<Color Us> unsigned long long perft(Position& p, unsigned int depth) {
	int nmoves; unsigned long long nodes = 0;
	MoveList<Us> list(p);
	if (depth == 1) return (unsigned long long) list.size();
	for (Move move : list) { p.play<Us>(move); nodes += perft<~Us>(p, depth - 1); p.undo<Us>(move); }
	return nodes;
}

template<Color Us> void perftdiv(std::string fen, unsigned int depth) {
	unsigned long long nodes = 0, pf;
	Position p;
	Position::set(fen, p);

	MoveList<Us> list(p);

	for (Move move : list) {
		std::cout << move <<"|";
		p.play<Us>(move);
		pf = perft<~Us>(p, depth - 1);
		std::cout << ": " << pf << " moves" << std::endl;
		nodes += pf;
		p.undo<Us>(move);
	}

	std::cout << "\nTotal: " << nodes << " moves\n";
}

void test_perft(int depth) {
	Position p;
	Position::set(DEFAULT_FEN, p);

	std::chrono::steady_clock::time_point begin = std::chrono::steady_clock::now();
	auto n = perft<WHITE>(p, depth);
	std::chrono::steady_clock::time_point end = std::chrono::steady_clock::now();
	auto diff = end - begin;

	unsigned long long nodes_correct = 119060324; /* depth == 6 */
	if (n == nodes_correct){ 
		std::cout << "NPS: " << int(n * 1000000.0 / std::chrono::duration_cast<std::chrono::microseconds>(diff).count()) << std::endl;
		std::cout << "Time difference = " << std::chrono::duration_cast<std::chrono::microseconds>(diff).count() << " [microseconds]" << std::endl;
		std::cout << "Nodes:" << n << " is correct" << std::endl << std::endl;
		std::cout << "TEST PASSED,"<< std::endl;

	}
	else{
		std::cerr << "TEST FAILED " << "expected Nodes:" << nodes_correct << " got Nodes:" << n << std::endl << std::endl;
	}

}

int main() {
	initialise_all_databases();
	zobrist::initialise_zobrist_keys();	

	//perftdiv<WHITE>(DEFAULT_FEN,5);

	int depth =6;
	std::cout << "Position: " << DEFAULT_FEN << std::endl << "Depth:" << depth << std::endl; 
    test_perft(depth);
}