#include <vector>
#include <string>
#include <cstring>
#include <cstdint>
#include <cstdlib>
#include <sstream>
#include <stdexcept>
#include "iostream"
#include "libsurge.h"
#include "libcmg.h"

using namespace std;

using u64 = std::uint64_t;
using i32 = std::int32_t;

#ifdef _surge_init__attribute__
	void surge_init(){
		initialise_all_databases(); 
		zobrist::initialise_zobrist_keys(); 
		return;
	};
#endif

namespace cmg {

	/************************************************************************** */
	CMGMove::CMGMove(int from, int to, int flags){
		Square _from = Square(from); 
		Square _to = Square(to); 
		MoveFlags _flags = MoveFlags(flags);
		Move _move(_from, _to, _flags); 
	};

	CMGMove::~CMGMove() {

	};

	void CMGMove::load(Move m){ 
		Move _move(m.from(), m.to(), m.flags()); 
	};

	Move CMGMove::m(){
		return _move;
	};
	/************************************************************************** */

	CMGPosition::CMGPosition () {
		// Default to the standard starting position; an empty board would leave
		// _state uninitialized and make move generation undefined (no kings)
		set_fen(DEFAULT_FEN);
	};
	
	CMGPosition::CMGPosition (std::string fen){
		try {
			set_fen(fen);
		} catch (const std::exception& e) {
			throw std::invalid_argument("Failed to initialize position from FEN: " + std::string(e.what()));
		}
	};
	
    CMGPosition::CMGPosition(std::vector<std::pair<int, int>> piecelist, bool turn, int epsq, std::string castling){
		// Validate input
		if (epsq < 0 || (epsq > 63 && epsq != 64)) {
			throw std::invalid_argument("Invalid en passant square: " + std::to_string(epsq));
		}
		
		std::vector<std::pair<Piece,Square>> surge_pc_list;
		for (const auto& i : piecelist){ 
			if (i.first < 0 || i.first >= 15 || i.second < 0 || i.second >= 64) {
				throw std::invalid_argument("Invalid piece or square in piece list");
			}
			std::pair<Piece,Square> _item(Piece(i.first), Square(i.second)); 
			surge_pc_list.push_back(_item); 
		};
		
		try {
			Position::set_position(surge_pc_list, (turn ? WHITE : BLACK), castling, Square(epsq), _position);
			_init();
		} catch (const std::exception& e) {
			throw std::invalid_argument("Failed to set position: " + std::string(e.what()));
		}
	};

	CMGPosition::~CMGPosition () { 
	
	};

	std::string CMGPosition::fen() { 
		return _position.fen();
	};
	
	void CMGPosition::set_fen(std::string fen) {
		try {
			Position::set(fen, _position); 
			_init();
		} catch (const std::exception& e) {
			throw std::invalid_argument("Invalid FEN string: " + fen);
		}
	};
	
	void CMGPosition::_init(){ 
		_position.checkers = 0;
		turn() == WHITE ? _states<WHITE>() : _states<BLACK>(); 
	};

	void CMGPosition::print(){ 
		std::cout << _position; 
	};

	Color CMGPosition::turn(){
		return _position.turn(); 
	};
	
	template<Color Us> void CMGPosition::play(CMGMove &move){
		_position.play<Us>(move.m());
		_init();
	};

	template<Color Us> void CMGPosition::undo(CMGMove &move){
		_position.undo<Us>(move.m());
		_init();
	};

	void CMGPosition::move_piece(std::int32_t from, std::int32_t to) {
		// Bounds checking
		if (from < 0 || from >= 64 || to < 0 || to >= 64) {
			throw std::out_of_range("Square index out of bounds. Must be 0-63, got from=" + 
									std::to_string(from) + ", to=" + std::to_string(to));
		}
		
		// Check if there's a piece at the source square
		if (_position.at(Square(from)) == NO_PIECE) {
			throw std::invalid_argument("No piece at source square " + std::to_string(from));
		}
		
		Piece pc { _position.at(Square(from)) };
		_position.remove_piece(Square(from));
		_position.put_piece(pc, Square(to));
		_init();
	};

	void CMGPosition::play_move(std::int32_t from, std::int32_t to, std::int32_t flags) {
		if (from < 0 || from >= 64 || to < 0 || to >= 64) {
			throw std::out_of_range("Square index out of bounds. Must be 0-63, got from=" +
									std::to_string(from) + ", to=" + std::to_string(to));
		}
		if (_position.at(Square(from)) == NO_PIECE) {
			throw std::invalid_argument("No piece at source square " + std::to_string(from));
		}

		const bool pawn_move = (type_of(_position.at(Square(from))) == PAWN);
		const bool capture = (flags & 0b1000) != 0;
		const Color mover = _position.turn();

		Move move{Square(from), Square(to), MoveFlags(flags)};
		mover == WHITE ? _position.play<WHITE>(move) : _position.play<BLACK>(move);

		_position.halfmove = (pawn_move || capture) ? 0 : _position.halfmove + 1;
		if (mover == BLACK) _position.fullmove++;
		_init();
	};

	void CMGPosition::put_piece(int pc, std::int32_t to) {
		if (to < 0 || to >= 64) {
			throw std::out_of_range("Square index out of bounds: " + std::to_string(to));
		}
		if (pc < 0 || pc >= 15) {
			throw std::invalid_argument("Invalid piece type: " + std::to_string(pc));
		}
		
		_position.put_piece(Piece(pc), Square(to)); 
		_init();
	};

    void CMGPosition::remove_piece(int sq){
		if (sq < 0 || sq >= 64) {
			throw std::out_of_range("Square index out of bounds: " + std::to_string(sq));
		}
		
		_position.remove_piece(Square(sq)); 
		_init();
	};

	std::vector<std::int32_t> CMGPosition::moves(int Us){
		if (Us == 0) return _moves<WHITE>();
		else if (Us == 1) return _moves<BLACK>();
		else throw std::invalid_argument("Color must be 0 (WHITE) or 1 (BLACK)");
	};
	
	template<Color Us> std::vector<std::int32_t> CMGPosition::_moves(){
		std::vector<std::int32_t> movelist {};
		if (_state < CMG_ILLEGAL_POSITION){
			MoveList<Us> move_list(_position);
			for (Move move : move_list) {
				movelist.push_back(move.from()); 
				movelist.push_back(move.to()); 
				movelist.push_back(move.flags());
			}
		}
		return movelist;
	};
	
	std::int64_t CMGPosition::perft(unsigned int depth){
		return turn() == WHITE ? _perft<WHITE>(depth) : _perft<BLACK>(depth);
	}

	template<Color Us>
	std::int64_t CMGPosition::_perft(unsigned int depth) {
		std::int64_t nodes = 0;
		if (_state >= CMG_ILLEGAL_POSITION) return 0; // Us in illegal position, no legal moves
		if (depth == 0) return 1; // depth is unsigned, without this base case depth-1 wraps around
		MoveList<Us> list(_position);
		if (depth == 1) return (std::int64_t) list.size();
		for (Move move : list) {
			_position.play<Us>(move);
			nodes += (std::int64_t) _perft<~Us>(depth - 1);
			_position.undo<Us>(move);
		}
		return nodes;
	}

	bool CMGPosition::is_legal(){
		return (_state < CMG_ILLEGAL_POSITION);
	}
	
	bool CMGPosition::_king_contact(){
		// Get king positions directly from bitboards for efficiency
		Square wk_sq = bsf(_position.bitboard_of(WHITE, KING));
		Square bk_sq = bsf(_position.bitboard_of(BLACK, KING));
		
		// Check if kings are adjacent (including diagonally)
		int file_diff = abs(file_of(wk_sq) - file_of(bk_sq));
		int rank_diff = abs(rank_of(wk_sq) - rank_of(bk_sq));
		
		return (file_diff <= 1 && rank_diff <= 1);
	};

	bool CMGPosition::_illegal_pawn(){
		// Optimized: Direct bitboard check instead of string parsing
		Bitboard white_pawns = _position.bitboard_of(WHITE, PAWN);
		Bitboard black_pawns = _position.bitboard_of(BLACK, PAWN);
		
		// Check if any pawns are on 1st or 8th rank
		return (white_pawns & (MASK_RANK[RANK1] | MASK_RANK[RANK8])) ||
		       (black_pawns & (MASK_RANK[RANK1] | MASK_RANK[RANK8]));
	};

	CMG_POSITION_STATE CMGPosition::state(int Us){ 
		if (Us != 0 && Us != 1) {
			throw std::invalid_argument("Color must be 0 (WHITE) or 1 (BLACK)");
		}
		return _state;
	}

	template<Color Us> void CMGPosition::_states() {
		bool us_check = _position.in_check<Us>();
		bool them_check = _position.in_check<~Us>();
		
		if (_illegal_pawn() || _king_contact() || them_check){
			_state = CMG_ILLEGAL_POSITION;
		}
		else{
			// _moves() consults _state, which this function is about to compute;
			// reset it first so a stale/uninitialized ILLEGAL value cannot
			// suppress move generation and misclassify the position as mate/stalemate
			_state = CMG_OPEN_STATE;
			std::vector<std::int32_t> move_list;
			move_list = _moves<Us>();
			if (move_list.size() == 0){
				_state = us_check ? CMG_CHECKMATE : CMG_STALEMATE;
			}
			else{
				_state = us_check ? CMG_CHECK : CMG_OPEN_STATE;
			}
		}
	}

	std::string sqstr(int idx){
		if (idx < 0 || idx > 64) {
			throw std::out_of_range("Square index must be 0-64, got " + std::to_string(idx));
		}
		return SQSTR[idx];
	}
	
	// Explicit template instantiations
	template void CMGPosition::play<WHITE>(CMGMove &move);
	template void CMGPosition::play<BLACK>(CMGMove &move);
	template void CMGPosition::undo<WHITE>(CMGMove &move);
	template void CMGPosition::undo<BLACK>(CMGMove &move);
	template std::vector<std::int32_t> CMGPosition::_moves<WHITE>();
	template std::vector<std::int32_t> CMGPosition::_moves<BLACK>();
	template std::int64_t CMGPosition::_perft<WHITE>(unsigned int depth);
	template std::int64_t CMGPosition::_perft<BLACK>(unsigned int depth);
	template void CMGPosition::_states<WHITE>();
	template void CMGPosition::_states<BLACK>();
};