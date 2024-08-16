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
            //loads emoty Position
            CMGPosition();

            //loads Position by fen string
            CMGPosition(std::string fen);
            
            //load position by position informations
            CMGPosition(std::vector<std::pair<int, int>> piecelist, bool turn, int epsq,  std::string castling);
            //unload position 
            ~CMGPosition();
            
            //returns the fen string of the position
            std::string fen();

            //loads the fen string
            void set_fen(std::string fen);

            //print the position as chess board 
            void print();

            //play a move
            template<Color Us> void play(CMGMove &move);

            //takes the move back
            template<Color Us> void undo(CMGMove &move);

            //put a piece at square  and init
	        void put_piece(int pc, std::int32_t to);

            //remove the piece at square and init
            void remove_piece(int sq);

            //move a piece from - to
            void move_piece(std::int32_t from, std::int32_t to);

            //perft test fro convinience
            std::int64_t perft(unsigned int depth);

            //perft test fro convinience
            std::vector<std::int64_t> perft_moves(unsigned int depth);


            //returns the color of the moving party
            Color turn();

            //position legel in the current posttion ans current moving party
            bool is_legal();

            //returns all moves in the setup
            std::vector<std::int32_t> moves(int us);

            //state of the position
            CMG_POSITION_STATE state(int us);
        private:
            Position _position;
            bool _king_contact();
            bool _illegal_pawn();
            bool _illegal_check();
            void _init();
            template<Color> void _states();
            template<Color Us> std::vector<std::int64_t> _perft_moves(unsigned int depth);
            template<Color> std::int64_t _perft(unsigned int depth);
            template<Color> std::vector<std::int32_t> _moves();  
            CMG_POSITION_STATE _state; //position state when it is Us's turn
    };
    std::string sqstr(int idx);
}

#endif
