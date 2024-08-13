// Example from https://www.diehlpk.de/blog/modern-cpp/
// g++-10 -O3 -pthread  -o thread_test threading1.cpp 
// ./thread_test 10000000 2

#include <cmath>
#include <cstdlib>
#include <future>
#include <vector>
#include <iostream>
#include <chrono>
#include "libsurge.h"
#include <locale>


template<Color Us> 
unsigned long long dist_perft(Position& p, unsigned int maxdepth) {
	unsigned long long nodes = 0;
	MoveList<Us> list(p);
	for (Move move : list) {
        p.play<Us>(move);
        nodes += perft_start<~Us>(p.fen(), maxdepth - 1);
        p.undo<Us>(move);
    }
    return nodes;
};

template<Color Us> 
unsigned long long perft_start(std::string fen, unsigned int depth) {
        long long result = 0; 
        Position next_pos; 
        Position::set(fen,next_pos);
    	MoveList<Us> list(next_pos);
        result = perft<Us>(next_pos, depth);
        return result;
}

template<Color Us> 
unsigned long long perft(Position& p, unsigned int depth) {
	unsigned long long nodes = 0;
	MoveList<Us> list(p);
	if (depth == 1) return (unsigned long long) list.size();
    for (Move move : list) {
        p.play<Us>(move); 
        nodes += perft<~Us>(p, depth - 1); 
        p.undo<Us>(move);
    }
    return nodes;
};

int main(int argc,char* argv[]){
    int maxdepth=atoi(argv[1]);
    
    std::cout.imbue(std::locale(""));

    initialise_all_databases();
	zobrist::initialise_zobrist_keys();	
    Position p;
    Position::set(DEFAULT_FEN, p);
	MoveList<WHITE> list(p);
    unsigned long long nodes = 0;
    std::vector<std::future<unsigned long long>> futures {};
    std::chrono::steady_clock::time_point begin {};
    std::chrono::steady_clock::time_point end {};


	begin = std::chrono::steady_clock::now();
    for (Move move : list) {
        p.play<WHITE>(move);
        futures.emplace_back(std::async(perft_start<BLACK>,p.fen(), maxdepth-1) );
        p.undo<WHITE>(move);
    }
    for (std::future<unsigned long long>& future: futures){ 
        nodes += future.get(); 
    }
    end = std::chrono::steady_clock::now();
    auto diff = end - begin;
    int count = std::chrono::duration_cast<std::chrono::microseconds>(diff).count();
    std::cout << " Nodes=" << nodes <<std::endl;
    std::cout << " Duration=" << count/1000 << " Milliseconds" << std::endl;
    std::cout << " NPS=" << nodes / (count / 1'000'000) << std::endl;
    return 0;
};