from board import Board
import random

class Game:
    def __init__(self):
        self.board = Board()
        self.current_player = "X"

    def start_game(self):
        print("Welcome to Tic Tac Toe!")
        self.board.initialize_board()
        self.display_board()

        while True:
            if self.current_player == "X":
                move = self.get_user_move()
                self.make_user_move(move)
            else:
                self.make_computer_move()

            self.display_board()

            if self.check_game_over():
                break

            self.current_player = "O" if self.current_player == "X" else "X"

        self.ask_play_again()

    def display_board(self):
        print("Current Board:")
        for row in self.board.board:
            print(" | ".join(row))
            print("---------")

    def get_user_move(self):
        while True:
            move = input("Enter your move (row column): ")
            try:
                row, col = map(int, move.split())
                if self.board.is_valid_move((row, col)):
                    return (row, col)
                else:
                    print("Invalid move. Please try again.")
            except ValueError:
                print("Invalid input. Please enter row and column numbers.")

    def make_user_move(self, move):
        self.board.update_board(move, "X")

    def make_computer_move(self):
        empty_squares = self.board.get_empty_squares()
        move = random.choice(empty_squares)
        self.board.update_board(move, "O")

    def check_game_over(self):
        if self.board.check_winner("X"):
            print("You win!")
            return True
        elif self.board.check_winner("O"):
            print("Computer wins!")
            return True
        elif self.board.is_board_full():
            print("It's a draw!")
            return True
        else:
            return False

    def ask_play_again(self):
        play_again = input("Do you want to play again? (yes/no): ")
        if play_again.lower() == "yes":
            self.start_game()
        else:
            print("Thank you for playing!")

if __name__ == "__main__":
    game = Game()
    game.start_game()
