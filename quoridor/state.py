from dataclasses import dataclass, field
import numpy as np
from collections import deque

BOARD_SIZE = 9
WALLS_PER_PLAYER = 10

@dataclass
class QuoridorState:
    # pawn positions as (row, col); player 0 starts at (0, BOARD_SIZE // 2), player 1 at (BOARD_SIZE - 1, BOARD_SIZE // 2)
    pawns: list = field(
        default_factory=lambda: [(0, BOARD_SIZE // 2), (BOARD_SIZE - 1, BOARD_SIZE // 2)]
    )
    
    # h_walls[r][c] = True means a horizontal wall blocks vertical movement
    # between rows r and r+1, spanning columns c and c+1
    h_walls: np.ndarray = field(
        default_factory=lambda: np.zeros((BOARD_SIZE - 1, BOARD_SIZE - 1), dtype=bool)
    )
    
    # v_walls[r][c] = True means a vertical wall blocks horizontal movement
    # between columns c and c+1, spanning rows r and r+1
    v_walls: np.ndarray = field(
        default_factory=lambda: np.zeros((BOARD_SIZE - 1, BOARD_SIZE - 1), dtype=bool)
    )

    walls_left: list = field(
        default_factory=lambda: [WALLS_PER_PLAYER, WALLS_PER_PLAYER]
    )
    current_player: int = 0  # 0 or 1

    # ------------------------------------------------------------------ #
    # Basic queries
    # ------------------------------------------------------------------ #
    def goal_row(self, player: int) -> int:
        return BOARD_SIZE - 1 if player == 0 else 0
    
    def is_terminal(self) -> bool:
        return self.pawns[0][0] == self.goal_row(0) or self.pawns[1][0] == self.goal_row(1)
    
    def winner(self) -> int | None:
        if self.pawns[0][0] == self.goal_row(0):
            return 0
        elif self.pawns[1][0] == self.goal_row(1):
            return 1
        else:
            return None

    # ------------------------------------------------------------------ #
    # Movement / adjacency
    # ------------------------------------------------------------------ #  
    def can_move_between(self, from_pos: tuple[int, int], to_pos: tuple[int, int]) -> bool:
        """Check if a wall blocks movement between two adjacent cells."""
        fr, fc = from_pos
        tr, tc = to_pos
        
        if not (0 <= tr < BOARD_SIZE and 0 <= tc < BOARD_SIZE):
            return False
        
        if abs(fr - tr) + abs(fc - tc) != 1:
            return False
        
        if fr == tr:  # horizontal move
            c = min(fc, tc)
            # vertical walls block horizontal movement (can start between rows fr-1 and fr, or between fr and fr+1)
            if fr < BOARD_SIZE - 1 and self.v_walls[fr, c]:
                return False
            if fr > 0 and self.v_walls[fr - 1, c]:
                return False
            return True
        else:  # vertical move
            r = min(fr, tr)
            # horizontal walls block vertical movement (can start between columns fc-1 and fc, or between fc and fc+1)
            if fc < BOARD_SIZE - 1 and self.h_walls[r, fc]:
                return False
            if fc > 0 and self.h_walls[r, fc - 1]:
                return False
            return True
    
    def legal_pawn_moves(self) -> list[tuple[int, int]]:
        """Return a list of legal pawn moves for the current player."""
        player = self.current_player
        opponent = 1 - player
        my_pos = self.pawns[player]
        opp_pos = self.pawns[opponent]
        mr, mc = my_pos

        moves = []
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = mr + dr, mc + dc
            if not (0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE):
                continue
            if not self.can_move_between(my_pos, (nr, nc)):
                continue
            if (nr, nc) == opp_pos:
                # try to jump over
                jr, jc = nr + dr, nc + dc
                if (0 <= jr < BOARD_SIZE and 0 <= jc < BOARD_SIZE) and self.can_move_between((nr, nc), (jr, jc)):
                    moves.append((jr, jc))
                else:
                    # diagonal jumps (perpendicular to current direction)
                    for ddr, ddc in [(dc, dr), (-dc, -dr)]:
                        sc, sr = nr + ddr, nc + ddc
                        if (0 <= sc < BOARD_SIZE and 0 <= sr < BOARD_SIZE) and self.can_move_between((nr, nc), (sc, sr)):
                            moves.append((sc, sr))
            else:
                moves.append((nr, nc))
        return moves
    
    # ------------------------------------------------------------------ #
    # Wall placement
    # ------------------------------------------------------------------ #
    def legal_wall_placements(self) -> list[tuple[int, int, str]]:
        """Return (row, col, orientation) tuples. Orientation in: {'h', 'v'}."""
        
        placements: list[tuple[int, int, str]] = []
        if self.walls_left[self.current_player] > 0:
            for r in range(BOARD_SIZE - 1):
                for c in range(BOARD_SIZE - 1):
                    if self._is_valid_wall_placement(r, c, 'h'):
                        placements.append((r, c, 'h'))
                    if self._is_valid_wall_placement(r, c, 'v'):
                        placements.append((r, c, 'v'))
        return placements

    def _is_valid_wall_placement(self, r: int, c: int, orientation: str) -> bool:
        """Check if placing a wall at (r, c) with the given orientation is valid."""
        # Check for overlap with existing walls
        if orientation == 'h':
            # horizontal wall at current anchor, anchor to left, or anchor to right
            if self.h_walls[r, c]:
                return False
            if c - 1 >= 0 and self.h_walls[r, c - 1]:
                return False
            if c + 1 <= BOARD_SIZE - 2 and self.h_walls[r, c + 1]:
                return False
            # vertical wall at current anchor
            if self.v_walls[r, c]:
                return False
        else:  # orientation == 'v'
            # vertical wall at current anchor, anchor above, or anchor below
            if self.v_walls[r, c]:
                return False
            if r - 1 >= 0 and self.v_walls[r - 1, c]:
                return False
            if r + 1 <= BOARD_SIZE - 2 and self.v_walls[r + 1, c]:
                return False
            # horizontal wall at current anchor
            if self.h_walls[r, c]:
                return False
        # Check that it doesn't block all paths for either player
        if orientation == 'h':
            self.h_walls[r, c] = True
        else:
            self.v_walls[r, c] = True
        valid = self._has_path_to_goal(0) and self._has_path_to_goal(1)
        if orientation == 'h':
            self.h_walls[r, c] = False
        else:
            self.v_walls[r, c] = False
        return valid
    
    def _has_path_to_goal(self, player: int) -> bool:
        """Check if the given player has a path from their pawn to their goal row."""
        start = self.pawns[player]
        goal_row = self.goal_row(player)
        visited = set()
        queue = deque([start])
        
        while queue:
            cell = queue.popleft()
            if cell in visited:
                continue
            visited.add(cell)
            r, c = cell
            if r == goal_row:
                return True
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                if (0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE) and self.can_move_between(cell, (nr, nc)):
                    queue.append((nr, nc))
        return False