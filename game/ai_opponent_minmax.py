from .board import Board
from .entities import Coord
from .ai_opponent_base import AIOpponentBase, methods


class AIOpponent(AIOpponentBase):
    def __init__(self, board: Board, method: methods, depth: int = 3):
        super().__init__(board, method)
        self._depth = depth

    @property
    def name(self) -> str:
        return 'AIOpponentMinmax'

    @property
    def description(self) -> str:
        return 'AIOpponentMinmax is a simple AI opponent that uses the minimax algorithm to find the best move.'

    @property
    def depth(self) -> int:
        return self._depth

    @staticmethod
    def _dest_y(piece) -> int:
        return piece.dest[1] if isinstance(piece.dest, tuple) else piece.dest

    @staticmethod
    def _forward_dir(piece) -> int:
        dest_y = AIOpponent._dest_y(piece)
        return 1 if dest_y > piece.loc[1] else -1

    @staticmethod
    def _gap_to_dest(piece, loc_y: int = None) -> int:
        dest_y = AIOpponent._dest_y(piece)
        y = piece.loc[1] if loc_y is None else loc_y
        return abs(y - dest_y)

    @staticmethod
    def _heuristic_for_move(board: Board, piece, move) -> int:
        # Positive if this move progresses toward destination, small bonus if onto a colored tile with a moving skill
        new_y = move[1]
        before_gap = AIOpponent._gap_to_dest(piece)
        after_gap = AIOpponent._gap_to_dest(piece, new_y)
        progress = before_gap - after_gap  # >0 means closer

        # Prefer landing on tiles that grant MoveExtended (more tempo next turns)
        skill = board.color_skills.get_skill(board.color_grid[new_y][move[0]]) if 0 <= new_y < board.h and 0 <= move[0] < board.w else None
        skill_bias = 1 if getattr(skill, 'name', '') == 'Move Extended' else 0

        # Anti-bounce and zero-progress penalty (ordering only; does not forbid moves)
        penalty = 0
        # Slightly penalize moves that don't improve distance
        if progress == 0:
            penalty -= 1
        elif progress < 0:
            penalty -= 2
        # Penalize immediate backtracking (moving back to the square this piece last moved from)
        if hasattr(board, 'move_history') and board.move_history:
            for kind, pid, frm, to in reversed(board.move_history):
                if kind == 'move' and pid == piece.piece_id:
                    if frm == move and to == piece.loc:
                        penalty -= 3
                    break

        return progress * 3 + skill_bias + penalty

    @staticmethod
    def _filter_skill_targets(board: Board, piece, skill, intensity):
        # Do not prune options; return all legal targets so minimax can decide.
        # Only exception: skip Color Swap for now (unfinished design and huge branching factor).
        skill_name = getattr(skill, 'name', '')
        if skill_name == 'Color Swap':
            return []
        return skill.get_legal_targets(board, piece, intensity)

    @staticmethod
    def _heuristic_for_skill(board: Board, piece, skill, target, intensity) -> int:
        name = getattr(skill, 'name', '')
        # Use turns-to-go minima delta before and after to score skills.
        # Higher heuristic => better for current player.
        # Copy is required to simulate skill application.
        import math

        # Baseline: current delta (opponent_min - us_min)
        us_turns_before, them_turns_before = (None, None)
        # get_turns_minima returns (p0, p1)
        p0_before, p1_before = board.get_turns_minima()

        # Simulate
        board_copy = board.copy()
        if hasattr(board_copy, '_suppress_logs'):
            board_copy._suppress_logs = True
        piece_copy = board_copy.pieces[piece.piece_id]
        t = target
        if isinstance(t, tuple) and len(t) == 2 and hasattr(t[0], 'piece_id'):
            t = (board_copy.pieces[t[0].piece_id], t[1])
        board_copy.color_skills.apply_skill(board_copy, piece_copy, t)
        p0_after, p1_after = board_copy.get_turns_minima()

        if board.turn == 0:
            delta_before = p1_before - p0_before
            delta_after = p1_after - p0_after
        else:
            delta_before = p0_before - p1_before
            delta_after = p0_after - p1_after

        return (delta_before - delta_after) * 10
        return 0

    @staticmethod
    def _find_best_move(board: Board, depth: int, original_depth: int, alpha: float, beta: float, maximizing_player: bool):
        if depth == 0 or board.winner() is not None:
            return board.get_score()

        # Root-level pre-scan: if any immediate winning action exists, take it.
        if depth == original_depth:
            current_player = board.turn
            for piece in board.pieces:
                if piece.player != current_player:
                    continue
                # Check normal moves for immediate wins
                for move in board.get_legal_moves(piece):
                    board_copy = board.copy()
                    if hasattr(board_copy, '_suppress_logs'):
                        board_copy._suppress_logs = True
                    piece_copy = board_copy.pieces[piece.piece_id]
                    board_copy.apply(piece_copy, move)
                    winner_id = board_copy.winner(return_ids=True)
                    if winner_id == piece.player:
                        return (piece.piece_id, move)

                # Check moving skills for immediate wins
                if piece.tile_color is not None:
                    skill = board.color_skills.get_skill(piece.tile_color)
                    if skill:
                        intensity = board.color_skills.get_intensity(board, piece.tile_color, piece.player)
                        if intensity > 0:
                            # Only moving-type skills can directly yield wins
                            if getattr(skill, 'skill_type', '') == 'moving':
                                targets = AIOpponent._filter_skill_targets(board, piece, skill, intensity)
                                for target in targets:
                                    board_copy = board.copy()
                                    if hasattr(board_copy, '_suppress_logs'):
                                        board_copy._suppress_logs = True
                                    piece_copy = board_copy.pieces[piece.piece_id]
                                    t = target
                                    if isinstance(t, tuple) and len(t) == 2 and hasattr(t[0], 'piece_id'):
                                        t = (board_copy.pieces[t[0].piece_id], t[1])
                                    board_copy.color_skills.apply_skill(board_copy, piece_copy, t)
                                    winner_id = board_copy.winner(return_ids=True)
                                    if winner_id == piece.player:
                                        if isinstance(target, tuple) and len(target) == 2 and hasattr(target[0], 'piece_id'):
                                            target_for_best = (target[0].piece_id, target[1])
                                        else:
                                            target_for_best = target
                                        return (piece.piece_id, target_for_best, 'skill')
        
        if maximizing_player:
            max_eval = float('-inf')
            best_move = None
            fallback_action = None
            
            for piece in board.pieces:
                if piece.player != board.turn:
                    continue
                
                # Get legal moves for this piece
                legal_moves = board.get_legal_moves(piece)

                actions = []
                for move in legal_moves:
                    h = AIOpponent._heuristic_for_move(board, piece, move)
                    actions.append(('move', piece.piece_id, move, h))

                # Consider skill usage if piece is not on a consumed tile
                if piece.tile_color is not None:
                    skill = board.color_skills.get_skill(piece.tile_color)
                    if skill:
                        intensity = board.color_skills.get_intensity(board, piece.tile_color, piece.player)
                        if intensity > 0:
                            filtered_targets = AIOpponent._filter_skill_targets(board, piece, skill, intensity)
                            for target in filtered_targets:
                                h = AIOpponent._heuristic_for_skill(board, piece, skill, target, intensity)
                                actions.append(('skill', piece.piece_id, target, h, skill))

                # Order actions by heuristic (desc for maximizing)
                actions.sort(key=lambda a: a[3], reverse=True)

                # Capture a simple fallback from the first available action
                if fallback_action is None and actions:
                    first = actions[0]
                    if first[0] == 'move':
                        fallback_action = (first[1], first[2])
                    else:
                        # normalize target to ids if MoveOpponent
                        tgt = first[2]
                        if isinstance(tgt, tuple) and len(tgt) == 2 and hasattr(tgt[0], 'piece_id'):
                            tgt = (tgt[0].piece_id, tgt[1])
                        fallback_action = (first[1], tgt, 'skill')

                for act in actions:
                    if act[0] == 'move':
                        _, pid, move, _ = act
                        board_copy = board.copy()
                        # Suppress logs on simulation copies
                        if hasattr(board_copy, '_suppress_logs'):
                            board_copy._suppress_logs = True
                        piece_copy = board_copy.pieces[pid]
                        board_copy.apply(piece_copy, move)
                        # Immediate-win shortcut at root depth
                        if depth == original_depth:
                            winner_id = board_copy.winner(return_ids=True)
                            if winner_id == piece_copy.player:
                                return (pid, move)
                        eval_score = AIOpponent._find_best_move(board_copy, depth - 1, original_depth, alpha, beta, not maximizing_player)
                        if eval_score > max_eval:
                            max_eval = eval_score
                            best_move = (pid, move)
                        alpha = max(alpha, eval_score)
                        if beta <= alpha:
                            break
                    else:
                        _, pid, target, _, skill = act
                        board_copy = board.copy()
                        if hasattr(board_copy, '_suppress_logs'):
                            board_copy._suppress_logs = True
                        piece_copy = board_copy.pieces[pid]
                        # Convert target to use pieces from board_copy (for MoveOpponent skill)
                        t = target
                        if isinstance(t, tuple) and len(t) == 2 and hasattr(t[0], 'piece_id'):
                            t = (board_copy.pieces[t[0].piece_id], t[1])
                        board_copy.color_skills.apply_skill(board_copy, piece_copy, t)
                        # Immediate-win shortcut at root depth for skill
                        if depth == original_depth:
                            winner_id = board_copy.winner(return_ids=True)
                            if winner_id == piece_copy.player:
                                if isinstance(target, tuple) and len(target) == 2 and hasattr(target[0], 'piece_id'):
                                    target_for_best = (target[0].piece_id, target[1])
                                else:
                                    target_for_best = target
                                return (pid, target_for_best, 'skill')
                        eval_score = AIOpponent._find_best_move(board_copy, depth - 1, original_depth, alpha, beta, not maximizing_player)
                        if eval_score > max_eval:
                            max_eval = eval_score
                            # convert back piece object to id for UI consumption if needed
                            if isinstance(target, tuple) and len(target) == 2 and hasattr(target[0], 'piece_id'):
                                target_for_best = (target[0].piece_id, target[1])
                            else:
                                target_for_best = target
                            best_move = (pid, target_for_best, 'skill')
                        alpha = max(alpha, eval_score)
                        if beta <= alpha:
                            break
                if beta <= alpha:
                    break
            
            if depth == original_depth:
                return best_move if best_move is not None else fallback_action
            else:
                return max_eval
        else:
            min_eval = float('inf')
            best_move = None
            fallback_action = None
            
            for piece in board.pieces:
                if piece.player != board.turn:
                    continue
                
                # Get legal moves for this piece
                legal_moves = board.get_legal_moves(piece)

                actions = []
                for move in legal_moves:
                    h = AIOpponent._heuristic_for_move(board, piece, move)
                    actions.append(('move', piece.piece_id, move, h))

                # Consider skill usage if piece is not on a consumed tile
                if piece.tile_color is not None:
                    skill = board.color_skills.get_skill(piece.tile_color)
                    if skill:
                        intensity = board.color_skills.get_intensity(board, piece.tile_color, piece.player)
                        if intensity > 0:
                            filtered_targets = AIOpponent._filter_skill_targets(board, piece, skill, intensity)
                            for target in filtered_targets:
                                h = AIOpponent._heuristic_for_skill(board, piece, skill, target, intensity)
                                actions.append(('skill', piece.piece_id, target, h, skill))

                # Order actions by heuristic (desc also for minimizing: good-for-current-player first)
                actions.sort(key=lambda a: a[3], reverse=True)

                # Capture a simple fallback from the first available action
                if fallback_action is None and actions:
                    first = actions[0]
                    if first[0] == 'move':
                        fallback_action = (first[1], first[2])
                    else:
                        tgt = first[2]
                        if isinstance(tgt, tuple) and len(tgt) == 2 and hasattr(tgt[0], 'piece_id'):
                            tgt = (tgt[0].piece_id, tgt[1])
                        fallback_action = (first[1], tgt, 'skill')

                for act in actions:
                    if act[0] == 'move':
                        _, pid, move, _ = act
                        board_copy = board.copy()
                        if hasattr(board_copy, '_suppress_logs'):
                            board_copy._suppress_logs = True
                        piece_copy = board_copy.pieces[pid]
                        board_copy.apply(piece_copy, move)
                        # Immediate-win shortcut at root depth
                        if depth == original_depth:
                            winner_id = board_copy.winner(return_ids=True)
                            if winner_id == piece_copy.player:
                                return (pid, move)
                        eval_score = AIOpponent._find_best_move(board_copy, depth - 1, original_depth, alpha, beta, not maximizing_player)
                        if eval_score < min_eval:
                            min_eval = eval_score
                            best_move = (pid, move)
                        beta = min(beta, eval_score)
                        if beta <= alpha:
                            break
                    else:
                        _, pid, target, _, skill = act
                        board_copy = board.copy()
                        if hasattr(board_copy, '_suppress_logs'):
                            board_copy._suppress_logs = True
                        piece_copy = board_copy.pieces[pid]
                        t = target
                        if isinstance(t, tuple) and len(t) == 2 and hasattr(t[0], 'piece_id'):
                            t = (board_copy.pieces[t[0].piece_id], t[1])
                        board_copy.color_skills.apply_skill(board_copy, piece_copy, t)
                        # Immediate-win shortcut at root depth for skill
                        if depth == original_depth:
                            winner_id = board_copy.winner(return_ids=True)
                            if winner_id == piece_copy.player:
                                if isinstance(target, tuple) and len(target) == 2 and hasattr(target[0], 'piece_id'):
                                    target_for_best = (target[0].piece_id, target[1])
                                else:
                                    target_for_best = target
                                return (pid, target_for_best, 'skill')
                        eval_score = AIOpponent._find_best_move(board_copy, depth - 1, original_depth, alpha, beta, not maximizing_player)
                        if eval_score < min_eval:
                            min_eval = eval_score
                            if isinstance(target, tuple) and len(target) == 2 and hasattr(target[0], 'piece_id'):
                                target_for_best = (target[0].piece_id, target[1])
                            else:
                                target_for_best = target
                            best_move = (pid, target_for_best, 'skill')
                        beta = min(beta, eval_score)
                        if beta <= alpha:
                            break
                if beta <= alpha:
                    break
            
            if depth == original_depth:
                return best_move if best_move is not None else fallback_action
            else:
                return min_eval


    def find_best_move(self) -> Coord:
        # Player 0 maximizes (positive scores), player 1 minimizes (negative scores)
        maximizing = self.board.turn == 0
        return self._find_best_move(self.board, self._depth, self._depth, float('-inf'), float('inf'), maximizing)