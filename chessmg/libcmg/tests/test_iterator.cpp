#include <cmath>
#include <iostream>
#include <sstream>
#include <locale>
#include <vector>
#include <cstdint>
#include <bitset>
#include <set>


#include "libsurge.h"
#include "libcmg.h"


// std::vector<std::uint8_t> i2p(std::uint32_t, const int length){
    
// }

int main(int argc, char* argv[]){
  
    std::cout.imbue(std::locale(""));
    const int NUMBER_OF_PIECES {4};
    const int MAX_THREADS {16};
    std::uint64_t ITERATOR_SIZE_PER_THREAD {1};
    for (int i=0; i< NUMBER_OF_PIECES;i++){
        ITERATOR_SIZE_PER_THREAD *= NSQUARES;
        std::cout << ITERATOR_SIZE_PER_THREAD <<std::endl;
    } 
    std::cout << NSQUARES << " " << ITERATOR_SIZE_PER_THREAD <<std::endl;
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

    std::uint32_t duplicates {0} ;
    std::vector<std::uint8_t> a;
    a.reserve(6);
    for (std::uint32_t v; v <ITERATOR_SIZE_PER_THREAD; v++ ){
        a[0] = (v >> 26) & 0b00111111;
        a[1] = (v >> 20) & 0b00111111;
        a[2] = (v >> 14) & 0b00111111;
        a[3] = (v >>  8) & 0b00111111;
        a[4] = (v >>  2) & 0b00111111;
        a[5] = (v >>  0) & 0b00000011;
        set<uint8_t> s(a.begin(), a.end());
        if (s.size() != a.size()) duplicates++;
        a.clear();
    }
    std::cout << duplicates;

};