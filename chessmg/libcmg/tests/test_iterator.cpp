#include <cmath>
#include <iostream>
#include <sstream>
#include <locale>
#include <vector>
#include <cstdint>
#include <bitset>
#include <set>
#include <chrono>

#include "libcmg.h"

    
int main(int argc, char* argv[]){
    std::cout.imbue(std::locale(""));
    std::chrono::steady_clock::time_point begin {};
    std::chrono::steady_clock::time_point end {};
 	
    std::vector<Piece> piecelist {WHITE_KING, BLACK_KING, WHITE_BISHOP,  BLACK_KNIGHT};
    std::uint64_t duplicates {0} ;
    std::vector<std::uint8_t> a;    
    int maxsize {3};
    int i = 0;
    std::uint64_t max {1};
    while (i<maxsize){
        max*=64;
        i++;
    }


    cmg::CMGPosition position("8/8/8/8/8/8/8/8 w - - 0 1");

    std::int64_t allmoves{0};
    //START
    std::cout << "Number of Pieces=" << maxsize << "\nIterations=" << max << std::endl;
    begin = std::chrono::steady_clock::now();    
    for (std::uint64_t v = 0; v <max; v++ ){
        for (int elem = 0; elem < maxsize; elem++){ 
            a.emplace_back(std::uint8_t((v >> (6*elem)) & 0b00111111)); 
        }
        std::set<std::uint8_t> s(a.begin(),a.end());
        if (s.size() != maxsize) {
            duplicates++;
        }
        else{
            for (int p=0; p<maxsize; p++){ position.put_piece(piecelist[p],a[p]);}
            allmoves += position.moves(0).size()/3;
            for (int p=0; p<maxsize; p++){ position.remove_piece(a[p]);}
        }
        a.clear(); 

    }

    //END
    end = std::chrono::steady_clock::now();    
    int count = std::chrono::duration_cast<std::chrono::microseconds>(end - begin).count();

    //RESULT    
    std::cout << "Duration=" << count << "\nDuplicates=" << duplicates << "\nAllmoves="<< allmoves << "\n" <<std::endl;

};


    // std::uint32_t v = 0xf0'f1'f2'f3 ;
    // std::cout << v <<std::endl;
    // std::vector<std::uint8_t> a;
    // a.reserve(6);
    // a[0] = (v >> 26) & 0b00111111;
    // a[1] = (v >> 20) & 0b00111111;
    // a[2] = (v >> 14) & 0b00111111;
    // a[3] = (v >>  8) & 0b00111111;
    // a[4] = (v >>  2) & 0b00111111;
    // a[5] = (v >>  0) & 0b00000011;
    // std::cout << std::bitset<32>(v) << std::endl;
    // std::cout << std::bitset<8>(a[0]) << std::endl;
    // std::cout << std::bitset<8>(a[1]) << std::endl;
    // std::cout << std::bitset<8>(a[2]) << std::endl;
    // std::cout << std::bitset<8>(a[3]) << std::endl;
    // std::cout << std::bitset<8>(a[4]) << std::endl;
    // std::cout << std::bitset<8>(a[5]) << std::endl;
