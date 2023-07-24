import random

class Board:
    def __init__(self):
        self.board = [" " for _ in range(9)]

    def clear_board(self):
        self.board = [" " for _ in range(9)]

    def display(self):
        print(f" {self.board[0]} | {self.board[1]} | {self.board[2]} ")
        print("---+---+---")
        print(f" {self.board[3]} | {self.board[4]} | {self.board[5]} ")
        print("---+---+---")
        print(f" {self.board[6]} | {self.board[7]} | {self.board[8]} ")

    def is_position_empty(self, position):
        return self.board[position - 1] == " "

    def is_board_full(self):
        return " " not in self.board

    def make_move(self, player, position):
        self.board[position - 1] = player.get_symbol()

    def is_winner(self, player):
        winning_combinations = [
            [0, 1, 2], [3, 4, 5], [6, 7, 8],  # Rows
            [0, 3, 6], [1, 4, 7], [2, 5, 8],  # Columns
            [0, 4, 8], [2, 4, 6]  # Diagonals
        ]

        for combination in winning_combinations:
            if all(self.board[pos] == player.get_symbol() for pos in combination):
                return True
        return False

    def get_random_empty_position(self):
        empty_positions = [pos + 1 for pos, value in enumerate(self.board) if value == " "]
        return random.choice(empty_positions)
