class Board:
    def __init__(self):
        self.board = []

    def initialize_board(self):
        self.board = [[" " for _ in range(3)] for _ in range(3)]

    def update_board(self, move, symbol):
        row, col = move
        self.board[row - 1][col - 1] = symbol

    def is_valid_move(self, move):
        row, col = move
        if 1 <= row <= 3 and 1 <= col <= 3:
            if self.board[row - 1][col - 1] == " ":
                return True
        return False

    def is_board_full(self):
        for row in self.board:
            if " " in row:
                return False
        return True

    def check_winner(self, symbol):
        for i in range(3):
            if self.board[i][0] == self.board[i][1] == self.board[i][2] == symbol:
                return True
            if self.board[0][i] == self.board[1][i] == self.board[2][i] == symbol:
                return True
        if self.board[0][0] == self.board[1][1] == self.board[2][2] == symbol:
            return True
        if self.board[0][2] == self.board[1][1] == self.board[2][0] == symbol:
            return True
        return False
