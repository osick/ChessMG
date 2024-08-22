#include <cstdlib>
#include <future>
#include <vector>
#include <iostream>
#include <chrono>
#include <locale>

#include "libsurge.h"

template<Color Us> 
unsigned long long perft_thread(std::string fen, unsigned int depth) {
        long long result = 0; 
        Position next_pos; 
        Position::set(fen,next_pos);
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

    //maxdepth from cli
    int maxdepth = argc>=2 ? atoi(argv[1]) : 6;

    //init libsurge
    initialise_all_databases();
	zobrist::initialise_zobrist_keys();	

    //start generating
    std::chrono::steady_clock::time_point begin {};
    std::chrono::steady_clock::time_point end {};
 	begin = std::chrono::steady_clock::now();
    Position p;
    Position::set(DEFAULT_FEN, p);
	MoveList<WHITE> list(p);
    unsigned long long nodes = 0;
    std::vector<std::future<unsigned long long>> futures {};

    //first step: split into different threads along the movelist in the starting position.
    for (Move move : list) {
        p.play<WHITE>(move);
            futures.emplace_back(std::async(perft_thread<BLACK>,p.fen(), maxdepth-1) );
        p.undo<WHITE>(move);
    }
    
    //second step: Collect the result from all futures.
    for (std::future<unsigned long long>& future: futures){ 
        nodes += future.get(); 
    }

    //Done.
    end = std::chrono::steady_clock::now();

    //Output of the result
    int count = std::chrono::duration_cast<std::chrono::microseconds>(end - begin).count();
    std::cout.imbue(std::locale(""));
    std::cout << "Nodes=" << nodes <<std::endl;
    std::cout << "Duration=" << count << " Mikroseconds" << std::endl;
    std::cout << "NPS=" << nodes / count * 1'000'000 << std::endl;
    
    return 0;
};