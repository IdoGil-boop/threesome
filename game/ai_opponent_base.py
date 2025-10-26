from abc import ABC, abstractmethod
from .board import Board
from .entities import Coord
import enum

methods = enum.Enum('methods', ['minimax'])

class AIOpponentBase(ABC):
    board: Board
    method: methods

    def __init__(self, board: Board, method: methods):
        self.board = board
        self.method = method

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        pass

    @abstractmethod
    def find_best_move(self) -> Coord:
        pass