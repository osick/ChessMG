"""
Test suite for the new chessmg API.

Tests the ChessPosition class and improved move generation API.
"""

import pytest
import numpy as np
from chessmg import (
    ChessPosition, Move, Color, PieceType, GameState,
    square_to_index, index_to_square
)


class TestSquareConversion:
    """Test square notation conversion functions."""
    
    def test_square_to_index(self):
        assert square_to_index("a1") == 0
        assert square_to_index("h1") == 7
        assert square_to_index("a8") == 56
        assert square_to_index("h8") == 63
        assert square_to_index("e4") == 28
    
    def test_index_to_square(self):
        assert index_to_square(0) == "a1"
        assert index_to_square(7) == "h1"
        assert index_to_square(56) == "a8"
        assert index_to_square(63) == "h8"
        assert index_to_square(28) == "e4"
    
    def test_invalid_square(self):
        with pytest.raises(ValueError):
            square_to_index("i1")
        with pytest.raises(ValueError):
            square_to_index("a9")
        with pytest.raises(ValueError):
            index_to_square(-1)
        with pytest.raises(ValueError):
            index_to_square(64)


class TestMove:
    """Test the Move class."""
    
    def test_move_creation(self):
        move = Move(12, 28)  # e2e4
        assert move.from_square == 12
        assert move.to_square == 28
        assert move.from_square_name == "e2"
        assert move.to_square_name == "e4"
        assert move.uci == "e2e4"
    
    def test_move_with_promotion(self):
        move = Move(52, 60, PieceType.QUEEN)  # e7e8q
        assert move.uci == "e7e8q"
        assert move.promotion == PieceType.QUEEN
    
    def test_move_from_uci(self):
        move = Move.from_uci("e2e4")
        assert move.from_square == 12
        assert move.to_square == 28
        assert move.promotion is None
        
        promo_move = Move.from_uci("e7e8q")
        assert promo_move.from_square == 52
        assert promo_move.to_square == 60
        assert promo_move.promotion == PieceType.QUEEN
    
    def test_invalid_move(self):
        with pytest.raises(ValueError):
            Move(-1, 28)
        with pytest.raises(ValueError):
            Move(12, 64)
        with pytest.raises(ValueError):
            Move.from_uci("e2")
        with pytest.raises(ValueError):
            Move.from_uci("e2e4x")


class TestChessPosition:
    """Test the ChessPosition class."""
    
    def test_starting_position(self):
        pos = ChessPosition()
        assert pos.turn == Color.WHITE
        assert not pos.is_check
        assert not pos.is_checkmate
        assert not pos.is_stalemate
        assert not pos.is_game_over
        assert len(pos.legal_moves()) == 20
    
    def test_fen_loading(self):
        # Test a specific position
        fen = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
        pos = ChessPosition(fen)
        assert pos.turn == Color.BLACK
        assert pos.fen == fen
    
    def test_invalid_fen(self):
        with pytest.raises(ValueError):
            ChessPosition("invalid fen string")
    
    def test_legal_moves_structure(self):
        pos = ChessPosition()
        moves = pos.legal_moves()
        
        # Check that we get Move objects
        assert all(isinstance(m, Move) for m in moves)
        
        # Check some known starting moves
        uci_moves = [m.uci for m in moves]
        assert "e2e4" in uci_moves
        assert "d2d4" in uci_moves
        assert "g1f3" in uci_moves
        assert "b1c3" in uci_moves
    
    def test_make_move_uci(self):
        pos = ChessPosition()
        initial_fen = pos.fen
        
        pos.make_move("e2e4")
        assert pos.turn == Color.BLACK
        assert pos.fen != initial_fen
        
        # Check that e4 is now occupied
        moves = pos.legal_moves()
        uci_moves = [m.uci for m in moves]
        assert "e7e5" in uci_moves
    
    def test_make_move_object(self):
        pos = ChessPosition()
        move = Move.from_uci("e2e4")
        pos.make_move(move)
        assert pos.turn == Color.BLACK
    
    def test_illegal_move(self):
        pos = ChessPosition()
        with pytest.raises(ValueError):
            pos.make_move("e2e5")  # Illegal pawn move
    
    def test_undo_move(self):
        pos = ChessPosition()
        initial_fen = pos.fen
        
        pos.make_move("e2e4")
        assert pos.fen != initial_fen
        
        undone_move = pos.undo_move()
        assert undone_move.uci == "e2e4"
        assert pos.fen == initial_fen
        
        # Test undo with no moves
        assert pos.undo_move() is None
    
    def test_checkmate_detection(self):
        # Fool's mate position
        pos = ChessPosition()
        pos.make_move("f2f3")
        pos.make_move("e7e5")
        pos.make_move("g2g4")
        pos.make_move("d8h4")
        
        assert pos.is_checkmate
        assert pos.is_game_over
        assert len(pos.legal_moves()) == 0
    
    def test_stalemate_detection(self):
        # Simple stalemate position
        fen = "7k/5Q2/6K1/8/8/8/8/8 b - - 0 1"
        pos = ChessPosition(fen)
        
        assert pos.is_stalemate
        assert pos.is_game_over
        assert not pos.is_check
        assert len(pos.legal_moves()) == 0
    
    def test_perft(self):
        pos = ChessPosition()
        
        # Known perft values for starting position
        assert pos.perft(0) == 1
        assert pos.perft(1) == 20
        assert pos.perft(2) == 400
        assert pos.perft(3) == 8902
        
        with pytest.raises(ValueError):
            pos.perft(-1)
    
    def test_copy(self):
        pos1 = ChessPosition()
        pos1.make_move("e2e4")
        
        pos2 = pos1.copy()
        assert pos1.fen == pos2.fen
        
        # Modifying copy shouldn't affect original
        pos2.make_move("e7e5")
        assert pos1.fen != pos2.fen


class TestBackwardCompatibility:
    """Test that old API still works with deprecation warnings."""
    
    def test_legacy_import_warning(self):
        with pytest.warns(DeprecationWarning):
            from chessmg import ChessMoveGeneratorCompat
    
    def test_legacy_moves_api(self):
        # Import the legacy API
        from chessmg import ChessMoveGenerator
        
        # Old API should still work
        pos = ChessMoveGenerator()
        
        # Test old moves() API - returns numpy array
        moves_array = pos.moves(as_string=False)
        assert isinstance(moves_array, np.ndarray)
        assert moves_array.shape == (20, 3)  # 20 moves, 3 values each
        
        # Test string API
        moves_str = pos.moves(as_string=True)
        assert len(moves_str) == 20
        assert all(isinstance(m, str) for m in moves_str)
        assert "e2-e4" in moves_str
    
    def test_new_moves_api(self):
        # Test that new API is better
        from chessmg import ChessMoveGenerator
        
        pos = ChessMoveGenerator()
        
        # New API returns Move objects
        moves = pos.legal_moves()
        assert len(moves) == 20
        assert all(hasattr(m, 'uci') for m in moves)
        assert all(hasattr(m, 'from_square') for m in moves)
        assert all(hasattr(m, 'to_square') for m in moves)


class TestAPIImprovements:
    """Test specific API improvements mentioned in the plan."""
    
    def test_moves_array_shape(self):
        """Test that moves() returns properly shaped array instead of flat list."""
        from chessmg import ChessMoveGenerator
        
        pos = ChessMoveGenerator()
        moves = pos.moves(as_string=False)
        
        # Should return (n_moves, 3) shaped array, not flat list
        assert isinstance(moves, np.ndarray)
        assert moves.ndim == 2
        assert moves.shape[1] == 3
        
        # Each row should be [from, to, flags]
        for move in moves:
            assert len(move) == 3
            assert 0 <= move[0] < 64  # from square
            assert 0 <= move[1] < 64  # to square
            assert 0 <= move[2] < 16  # flags
    
    def test_move_objects_api(self):
        """Test the new Move objects API."""
        pos = ChessPosition()
        moves = pos.legal_moves()
        
        # Should return list of Move objects with useful properties
        for move in moves:
            assert isinstance(move, Move)
            assert hasattr(move, 'from_square')
            assert hasattr(move, 'to_square')
            assert hasattr(move, 'uci')
            assert hasattr(move, 'from_square_name')
            assert hasattr(move, 'to_square_name')
            
            # Test that properties work
            assert move.from_square_name == index_to_square(move.from_square)
            assert move.to_square_name == index_to_square(move.to_square)
            assert move.uci == f"{move.from_square_name}{move.to_square_name}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])