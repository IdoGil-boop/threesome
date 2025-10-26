import pytest
from game import Board, Piece, Coord


def test_board_initialization():
    board = Board(8, 8)
    assert board.w == 8
    assert board.h == 8
    assert len(board.pieces) == 6  # 3 pieces per player
    assert board.turn == 1


def test_create_pieces():
    pieces = Board.create_pieces(8, 8, num_pieces=3)
    assert len(pieces) == 6
    
    # Check player 0 pieces are at y=0
    player_0_pieces = [p for p in pieces if p.player == 0]
    assert len(player_0_pieces) == 3
    assert all(p.loc[1] == 0 for p in player_0_pieces)
    
    # Check player 1 pieces are at y=7
    player_1_pieces = [p for p in pieces if p.player == 1]
    assert len(player_1_pieces) == 3
    assert all(p.loc[1] == 7 for p in player_1_pieces)


def test_in_bound():
    board = Board(8, 8)
    assert board.in_bound((0, 0)) == True
    assert board.in_bound((7, 7)) == True
    assert board.in_bound((4, 4)) == True
    assert board.in_bound((-1, 0)) == False
    assert board.in_bound((0, -1)) == False
    assert board.in_bound((8, 0)) == False
    assert board.in_bound((0, 8)) == False


def test_legal_moves():
    board = Board(8, 8, num_of_pieces=1)
    moves = board.legal_moves(distance=1)
    
    # Player 1's turn, should have moves for player 1's piece
    assert len(moves) > 0
    assert all(piece == board.pieces[1] for piece, dest in moves)
    assert len(moves) == 3
    board.turn = 0 # switch turns
    moves = board.legal_moves(distance=1)
    assert len(moves) == 3
    assert board.pieces[0].player != board.pieces[1].player

    board = Board(8, 8, num_of_pieces=2)
    moves = board.legal_moves(distance=1)
    assert len(moves) == 6
    board.turn = 0 # switch turns
    moves = board.legal_moves(distance=1)
    assert len(moves) == 6
    assert board.pieces[0].player != board.pieces[-1].player
    


def test_apply_move():
    board = Board(8, 8, num_of_pieces=1)
    piece = board.pieces[1]
    original_loc = piece.loc
    
    # Move piece down one square
    new_loc = (original_loc[0], original_loc[1] - 1)
    
    board.apply(piece, new_loc)
    
    # Check piece moved
    assert piece.loc == new_loc
    assert board.grid[new_loc[1]][new_loc[0]] == piece.piece_id
    assert board.grid[original_loc[1]][original_loc[0]] is None
    
    # Check turn changed
    assert board.turn == 0


def test_winner():
    board = Board(8, 8, num_of_pieces=1)
    
    # No winner initially
    assert board.winner() is None
    
    # Move player 0's piece to winning position (y=7)
    player_0_piece = board.pieces[0]
    player_0_piece.loc = (player_0_piece.loc[0], 7)
    assert board.winner() == 0
    
    # Reset and test player 1 win
    board = Board(8, 8, num_of_pieces=1)
    player_1_piece = board.pieces[1]
    player_1_piece.loc = (player_1_piece.loc[0], 0)
    assert board.winner() == 1


def test_piece_dataclass():
    piece = Piece(piece_id=0, player=0, loc=(2, 3), color=None)
    assert piece.piece_id == 0
    assert piece.player == 0
    assert piece.loc == (2, 3)
