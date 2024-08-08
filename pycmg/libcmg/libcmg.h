#ifndef LIBCMG_H
#define LIBCMG_H
#include <cstdint>
#include <vector>
#include <string>
#include "libsurge.h"

enum CMG_POSITION_STATE : uint8_t {
	CMG_CHECKMATE           = 0b00000000, //0
	CMG_STALEMATE           = 0b00000010, //2
	CMG_CHECK               = 0b00000100, //4
    CMG_OPEN_STATE          = 0b00100000, //32
	CMG_ILLEGAL_POSITION    = 0b10000000, //128
	CMG_ILLEGAL_PAWN_SQUARE = 0b10001000, //136
	CMG_ILLEGAL_KING_CONTACT= 0b10010000, //144
};

#undef  _surge_init__attribute__
#ifndef _surge_init__attribute__
    // The two methods must be called to init the shared library libsurge and so libcmg
        static bool surge_init =[](){
            initialise_all_databases(); 
            zobrist::initialise_zobrist_keys(); 
            return true;
    }();
#else
    // Alternativ method to init shared libsurge. Perhaps useful in platform independent setups....
    void surge_init() __attribute__((constructor));
#endif

namespace cmg{
    class CMGMove {
        public:
            CMGMove(int from, int to, int flags);
            ~CMGMove();
            Move m();
            void load(Move m);

        private:
            Move _move;
    };

    class CMGPosition {
        public:
            CMGPosition();
            CMGPosition(std::string fen);
            CMGPosition(std::vector<std::pair<int, int>> piecelist, bool turn, int epsq,  std::string castling);
            ~CMGPosition();
            std::string fen();
            void print();
            template<Color Us> void play(CMGMove &move);
            template<Color Us> void undo(CMGMove &move);
            void move_piece(std::int32_t from, std::int32_t to);
            std::int64_t perft(unsigned int depth);
            Color turn();
            bool is_legal();
            std::vector<std::int32_t> moves(int us);
            CMG_POSITION_STATE state(int us);
        private:
            Position _position;
            void set_fen(std::string fen);
            bool _king_contact();
            bool _illegal_pawn();
            void _set_states();
            std::int64_t _perft_w(unsigned int depth);
            std::int64_t _perft_b(unsigned int depth);
            void _w_moves(); 
            void _b_moves(); 
            std::vector<std::int32_t> _w_move_list;
            std::vector<std::int32_t> _b_move_list;
            CMG_POSITION_STATE _w_state; //position state when it is white's turn
            CMG_POSITION_STATE _b_state; //position state when it is black's turn
    };
    std::string sqstr(int idx);
}

#endif
