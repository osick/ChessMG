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


namespace cmg {
	CPosition::CPosition () {
	};
	
	CPosition::CPosition (std::string fen){
		Position::set(fen,_position); 
		_set_states();
	};
	
	CPosition::~CPosition () { 

	};

	std::string CPosition::fen() { 
		return _position.fen();
	};
	
	void CPosition::set_fen(std::string fen) {
		Position::set(fen,_position);
		_set_states();
	};
	
	void CPosition::print(){ 
		std::cout << _position; 
	};

	std::vector<std::uint64_t> CPosition::all_pieces(){
		vector<u64> arr;
		arr.push_back(_position.all_pieces<WHITE>());
		arr.push_back(_position.all_pieces<BLACK>());
		return arr;
	};

	Color CPosition::turn(){ 
		return _position.turn(); 
	};
	
	template<Color Us> 
	void CPosition::play(Move &move){
		return _position.play<Us>(move);
	}

	template<Color Us> 
	void CPosition::undo(Move &move){
		return _position.undo<Us>(move);	
	}

	void CPosition::move_piece(std::int32_t from, std::int32_t to) { 
		_position.move_piece(Square(from),Square(to)); 
	};
	
	std::vector<std::int32_t> CPosition::get_w_moves(){
		vector<i32> arr;
		if (_w_state < CMG_ILLEGAL_POSITION){
			MoveList<WHITE> move_list(_position);
			for (Move move : move_list) {
				arr.push_back(move.from()); 
				arr.push_back(move.to()); 
				arr.push_back(move.flags());}
		}
		return arr;
	};		
	
	std::vector<std::int32_t> CPosition::get_b_moves(){
		vector<i32> arr;
		if (_b_state < CMG_ILLEGAL_POSITION){
			MoveList<BLACK> move_list(_position);
			for (Move move : move_list) {
				arr.push_back(move.from()); 
				arr.push_back(move.to()); 
				arr.push_back(move.flags());}
		}
		return arr;
	};		

	std::int64_t CPosition::perft_w(unsigned int depth) {
		std::int64_t nodes = 0;
		if (not is_legal()) return 0;
		bool b_check = _position.in_check<BLACK>();
		MoveList<WHITE> list(_position);
		if (depth == 1) return (std::int64_t) list.size();
			for (Move move : list) {
				if (not b_check){
					_position.play<WHITE>(move);
					nodes += (std::int64_t) perft_b(depth - 1);
					_position.undo<WHITE>(move);
				}
			}

		return nodes;
	}

	std::int64_t CPosition::perft_b(unsigned int depth) {
		std::int64_t nodes = 0;
		if (not is_legal()) return 0;
		bool w_check = _position.in_check<WHITE>();
		MoveList<BLACK> list(_position);
		if (depth == 1) return (std::int64_t) list.size();
		for (Move move : list) {
			if (not w_check){
				_position.play<BLACK>(move);
				nodes += (std::int64_t) perft_w(depth - 1);
				_position.undo<BLACK>(move);
			}
		}
		return nodes;
	}

	bool CPosition::is_legal(){
		switch (turn()){
		case WHITE: 
			return (_w_state < CMG_ILLEGAL_POSITION);
		default: 
			return (_b_state < CMG_ILLEGAL_POSITION); 
		}
	}
	
	bool CPosition::_king_contact(){
		string fen = _position.fen();
		int wksq = a8;
		int bksq = a8;
		for (char ch : fen.substr(0, fen.find('K'))) { if (isdigit(ch)) wksq += (ch - '0') * EAST; else if (ch == '/') wksq += 2 * SOUTH; else wksq += 1;}
		for (char ch : fen.substr(0, fen.find('k'))) { if (isdigit(ch)) bksq += (ch - '0') * EAST; else if (ch == '/') bksq += 2 * SOUTH; else bksq += 1;}
		int result=abs(wksq-bksq);
		return (result ==1 or result ==7 or result ==8 or result ==9);
	};

	bool CPosition::_illegal_pawn(){
		string fen = _position.fen();
		std::string startstring;
		std::stringstream s;
		s << fen.substr(0, fen.find('/')) << fen.substr(fen.find_last_of('/'), fen.find(' ')); //first and last row string
		startstring = s.str(); 
		return (startstring.find("P") != string::npos or startstring.find("p") != string::npos);
	};

    CMG_POSITION_STATE CPosition::btm_state(){
		return _b_state;
	}

    CMG_POSITION_STATE CPosition::wtm_state(){
		return _w_state;
	};

	void CPosition::_set_states() {
		bool w_check  = _position.in_check<WHITE>();
		bool b_check  = _position.in_check<BLACK>();
		if (_illegal_pawn() or _king_contact() or (w_check and b_check)){
			_w_state = CMG_ILLEGAL_POSITION;
			_b_state = CMG_ILLEGAL_POSITION;
		}
		else{
			MoveList<WHITE> w_list(_position);
			if (w_check){
				_b_state = CMG_ILLEGAL_POSITION; // white is in check and it is blacks's turn
				if (w_list.size()==0){
					_w_state = CMG_CHECKMATE; //white has no move and white is in check
				}
			}else if (w_list.size()==0) {
				_w_state = CMG_STALEMATE; //no white move and white is not in check 
			}else{
				_w_state = CMG_OPEN_STATE;
			}

			MoveList<BLACK> b_list(_position);
			if (b_check){
				_w_state = CMG_ILLEGAL_POSITION; // black is in check and it is white's turn
				if (b_list.size()==0){
					_b_state = CMG_CHECKMATE; //black has no move and black is in check
				} 
			}else if (b_list.size()==0) {
				_b_state = CMG_STALEMATE; //no black move and black is not in check 
			}else{
				_b_state = CMG_OPEN_STATE;
			}
		}
		
	}

	std::string sqstr(int idx){
		return  SQSTR[idx];
	}
};
