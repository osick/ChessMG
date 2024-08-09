#ifndef LIBITER_H
#define LIBITER_H
#include <cstdint>
#include <vector>
#include <string>
#include "libsurge.h"
#include "libcmg.h"


namespace cmg{
    class Iterator {
        public:
            Iterator(std::vector<Piece> piecelist);
            ~Iterator();
            std::vector<Square> next(int index);

        private:
            CMGPosition         _cmg;
            int64_t             _idx;
            std::vector<Square> _pos_idx;
            Square              _next_sq(Square sq);
    };
}

#endif