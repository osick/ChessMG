#include <iostream>
#include <chrono>
#include "libcmg.h"

void test_perft(int depth) {
    cmg::CMGPosition p("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1");
	std::chrono::steady_clock::time_point begin = std::chrono::steady_clock::now();
	auto n =  p.perft(depth);
	std::chrono::steady_clock::time_point end = std::chrono::steady_clock::now();
	auto diff = end - begin;

    unsigned long long nodes_correct;

	if (depth == 6) nodes_correct = 119060324; 
	if (depth == 7) nodes_correct = 3195901860;
    
	if (n == nodes_correct){ 
		std::cout << "NPS: " << int(n * 1000000.0 / std::chrono::duration_cast<std::chrono::microseconds>(diff).count()) << std::endl;
		std::cout << "Time difference = " << std::chrono::duration_cast<std::chrono::microseconds>(diff).count() << " [microseconds]" << std::endl;
		std::cout << "Nodes:" << n << " is correct" << std::endl;
		std::cout << "TEST PASSED,"<< std::endl << std::endl;
	}
	else{
		std::cerr << "TEST FAILED " << "expected Nodes:" << nodes_correct << " got Nodes:" << n << std::endl << std::endl;
	}

}

int main() {
	// initialise_all_databases();
	// zobrist::initialise_zobrist_keys();	
	//perftdiv<WHITE>(DEFAULT_FEN,5);

	int depth = 6;
	std::cout << "Position: " << DEFAULT_FEN << std::endl << "Depth:" << depth << std::endl; 
    test_perft(depth);
}