from quoridor.state import QuoridorState

def test_starting_position():
    s = QuoridorState()
    assert s.pawns == [(0, 4), (8, 4)]
    assert s.walls_left == [10, 10]
    assert s.current_player == 0
    assert not s.is_terminal()

def test_starting_legal_moves():
    s = QuoridorState()
    moves = s.legal_pawn_moves()
    # from (0, 4) with no walls and no opponent adjacent, player 0 can move to
    # (1, 4), (0, 3), (0, 5). Can't go to (-1, 4) — off board.
    assert set(moves) == {(1, 4), (0, 3), (0, 5)}

def test_blocked_by_wall():
    s = QuoridorState()
    s.h_walls[0, 3] = True  # horizontal wall blocks (0,4)<->(1,4) via column 3-4 gap
    # Actually with h_walls[0, 3] = True, the wall spans columns 3 and 4 at row gap 0-1,
    # which blocks vertical movement from (0,3)<->(1,3) and (0,4)<->(1,4)
    moves = s.legal_pawn_moves()
    assert (1, 4) not in moves