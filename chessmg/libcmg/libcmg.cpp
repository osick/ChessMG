#include <vector>
#include <string>
#include <cstring>
#include <cstdint>
#include <cstdlib>
#include <sstream>
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

	};
	
	CMGPosition::CMGPosition (std::string fen){
		set_fen(fen);
	};
	
    CMGPosition::CMGPosition(std::vector<std::pair<int, int>> piecelist, bool turn, int epsq,  std::string castling){
		std::vector<std::pair<Piece,Square>> surge_pc_list;
		for (std::pair<int,int> i: piecelist){ 
			std::pair<Piece,Square> _item(Piece(i.first), Square(i.second)); 
			surge_pc_list.push_back(_item); 
		};
		Position::set_position(surge_pc_list, (turn ? WHITE : BLACK ), castling, Square(epsq), _position);
	};

	CMGPosition::~CMGPosition () { 
	
	};

	std::string CMGPosition::fen() { 
		return _position.fen();
	};
	
	void CMGPosition::set_fen(std::string fen) {
		Position::set(fen,_position); 
		_init();
	};
	
	void CMGPosition::_init(){ 
		turn()==WHITE ? _states<WHITE>() : _states<BLACK>(); 
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
		Piece pc { _position.at(Square(from)) };
		_position.remove_piece(Square(from));
		_position.put_piece(pc, Square(to)); 
		_position.checkers=0;
		_init();
	};
	
	std::vector<std::int32_t> CMGPosition::moves(int Us){
		if (Us == 0) return _moves<WHITE>() ;
		else return _moves<BLACK>(); 
	};
	
	template<Color Us> std::vector<std::int32_t>  CMGPosition::_moves(){
			std::vector<std::int32_t> movelist {};
			if (_state < CMG_ILLEGAL_POSITION){
			MoveList<Us> move_list(_position);
			for (Move move : move_list) {
				movelist.push_back(move.from()); 
				movelist.push_back(move.to()); 
				movelist.push_back(move.flags());}
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
		MoveList<Us> list(_position);
		if (depth == 1) return (std::int64_t) list.size();
		for (Move move : list) {
				_position.play<Us>(move);
				nodes += (std::int64_t) _perft<~Us>(depth - 1);
				_position.undo<Us>(move);
		}
		return nodes;
	}

	// template<Color Us>
    // std::vector<std::int64_t> CMGPosition::_perft_moves(unsigned int depth){
	// 	std::vector<std::int64_t> node_list {};	
	// 	if (_state >= CMG_ILLEGAL_POSITION) {
	// 		return node_list;
	// 	} // Us in illegal position, no legal moves
	// 	MoveList<Us> list(_position);
	// 	if (depth == 1) return (std::int64_t) list.size();
	// 	for (Move move : list) {
	// 			_position.play<Us>(move);
	// 			nodes += (std::int64_t) _perft<~Us>(depth - 1);
	// 			_position.undo<Us>(move);
	// 	}
	// 	return nodes;
	// }


	bool CMGPosition::is_legal(){
		return (_state  < CMG_ILLEGAL_POSITION);
	}
	
	bool CMGPosition::_king_contact(){
		string fen = _position.fen();
		int wksq = a8;
		int bksq = a8;
		for (char ch : fen.substr(0, fen.find('K'))) { if (isdigit(ch)) wksq += (ch - '0') * EAST; else if (ch == '/') wksq += 2 * SOUTH; else wksq += 1;}
		for (char ch : fen.substr(0, fen.find('k'))) { if (isdigit(ch)) bksq += (ch - '0') * EAST; else if (ch == '/') bksq += 2 * SOUTH; else bksq += 1;}
		int result=abs(wksq-bksq);
		return (result ==1 or result ==7 or result ==8 or result ==9);
	};

	bool CMGPosition::_illegal_pawn(){
		string fen = _position.fen();
		std::string startstring;
		std::stringstream s;
		s << fen.substr(0, fen.find('/')) << fen.substr(fen.find_last_of('/'), fen.find(' ')); //first and last row string
		startstring = s.str(); 
		return (startstring.find("P") != string::npos or startstring.find("p") != string::npos);
	};

	CMG_POSITION_STATE CMGPosition::state(int Us){ 
		return _state;
	}

	template<Color Us> void CMGPosition::_states() {
		bool us_check   = _position.in_check<Us>();
		bool them_check = _position.in_check<~Us>();
		if (_illegal_pawn() or _king_contact() or them_check){
			_state  = CMG_ILLEGAL_POSITION;
		}
		else{
			std::vector<std::int32_t>move_list;
			move_list = _moves<Us>();
			if (move_list.size()==0){
				_state = us_check? CMG_CHECKMATE : CMG_STALEMATE;
			}
			else{
				_state = CMG_OPEN_STATE;
			} // no special position
		}
		
	}

	std::string sqstr(int idx){
		return  SQSTR[idx];
	}
};
