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

	CMGMove::CMGMove(int from, int to, int flags){
		Square _from = Square(from); 
		Square _to = Square(to); 
		MoveFlags _flags = MoveFlags(flags);
		Move _move(_from, _to, _flags); 
	};

	CMGMove::~CMGMove() {};

	void CMGMove::load(Move m){ Move _move(m.from(), m.to(), m.flags()); };

	Move CMGMove::m(){return _move;};

	CMGPosition::CMGPosition () {};
	
	CMGPosition::CMGPosition (std::string fen){Position::set(fen,_position); _set_states();};
	
    CMGPosition::CMGPosition(std::vector<std::pair<int, int>> piecelist, bool turn, int epsq,  std::string castling){
		std::vector<std::pair<Piece,Square>> surge_pc_list;
		for (std::pair<int,int> i: piecelist){ 
			std::pair<Piece,Square> _item(Piece(i.first), Square(i.second)); 
			surge_pc_list.push_back(_item); 
		};
		Position::set_position(surge_pc_list, (turn ? WHITE : BLACK ), castling, Square(epsq), _position);
	};

	CMGPosition::~CMGPosition () { };

	std::string CMGPosition::fen() { return _position.fen();};
	
	void CMGPosition::set_fen(std::string fen) {Position::set(fen,_position); _set_states();};
	
	void CMGPosition::print(){ std::cout << _position; };

	Color CMGPosition::turn(){ return _position.turn(); };
	
	template<Color Us> void CMGPosition::play(CMGMove &move){ _position.play<Us>(move.m());};

	template<Color Us> void CMGPosition::undo(CMGMove &move){ _position.undo<Us>(move.m());};

	void CMGPosition::move_piece(std::int32_t from, std::int32_t to) { _position.move_piece(Square(from),Square(to)); _set_states(); };
	
	void CMGPosition::del_piece(Square sq){
	};
	
	void CMGPosition::add_piece(Piece pc, Square sq){
	};


	std::vector<std::int32_t> CMGPosition::moves(int Us){return (Us == 0 ? this->_w_move_list : this->_b_move_list); };
	
	void CMGPosition::_w_moves(){

		if (_w_state < CMG_ILLEGAL_POSITION){
			MoveList<WHITE> move_list(_position);
			for (Move move : move_list) {
				this->_w_move_list.push_back(move.from()); 
				this->_w_move_list.push_back(move.to()); 
				this->_w_move_list.push_back(move.flags());}
		}
	};
	
	void CMGPosition::_b_moves(){
		if (_b_state < CMG_ILLEGAL_POSITION){
			MoveList<BLACK> move_list(_position);
			for (Move move : move_list) {
				this->_b_move_list.push_back(move.from()); 
				this->_b_move_list.push_back(move.to()); 
				this->_b_move_list.push_back(move.flags());}
		}
	};		

	std::int64_t CMGPosition::perft(unsigned int depth){
		if (turn() == WHITE){ return _perft_w(depth); }
		else { return _perft_b(depth); }
	}

	std::int64_t CMGPosition::_perft_w(unsigned int depth) {
		std::int64_t nodes = 0;
		if (_w_state >= CMG_ILLEGAL_POSITION) return 0; // white to move illegal position, no legal moves
		MoveList<WHITE> list(_position);
		if (depth == 1) return (std::int64_t) list.size();
			for (Move move : list) {
				_position.play<WHITE>(move);
				nodes += (std::int64_t) _perft_b(depth - 1);
				_position.undo<WHITE>(move);
			}
		return nodes;
	}

	std::int64_t CMGPosition::_perft_b(unsigned int depth) {
		std::int64_t nodes = 0;
		if (_b_state >= CMG_ILLEGAL_POSITION) return 0; // black to move illegal position, no legal moves
		MoveList<BLACK> list(_position);
		if (depth == 1) return (std::int64_t) list.size();
		for (Move move : list) {
				_position.play<BLACK>(move);
				nodes += (std::int64_t) _perft_w(depth - 1);
				_position.undo<BLACK>(move);
		}
		return nodes;
	}

	bool CMGPosition::is_legal(){ return (turn() == WHITE ? (_w_state < CMG_ILLEGAL_POSITION) : (_b_state < CMG_ILLEGAL_POSITION));}
	
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

	CMG_POSITION_STATE CMGPosition::state(int Us){ return (Us == 0 ? _w_state : _b_state);}

	void CMGPosition::_set_states() {
		bool w_check  = _position.in_check<WHITE>();
		bool b_check  = _position.in_check<BLACK>();
		if (_illegal_pawn() or _king_contact() or (w_check and b_check)){
			_w_state = CMG_ILLEGAL_POSITION;
			_b_state = CMG_ILLEGAL_POSITION;
		}
		else{
			_w_moves();
			if (w_check){
				_b_state = CMG_ILLEGAL_POSITION; // white is in check and it is blacks's turn
				if (this->_w_move_list.size()==0){
					_w_state = CMG_CHECKMATE; //white has no move and white is in check
				}
			}else if (this->_w_move_list.size()==0) {
				_w_state = CMG_STALEMATE; //no white move and white is not in check 
			
			}else{
				_w_state = CMG_OPEN_STATE; // no special position
			}
			_b_moves();
			if (b_check){
				_w_state = CMG_ILLEGAL_POSITION; // black is in check and it is white's turn
				if (this->_b_move_list.size()==0){
					_b_state = CMG_CHECKMATE; //black has no move and black is in check
				} 
			}else if (this->_b_move_list.size()==0) {
				_b_state = CMG_STALEMATE; //no black move and black is not in check 
			}else{
				_b_state = CMG_OPEN_STATE; // no special position
			}
		}
		
	}

	std::string sqstr(int idx){
		return  SQSTR[idx];
	}
};
