from board import Board
from player import Player

class Game:
    def __init__(self):
        self.board = Board()
        self.player = Player("Player", "X")
        self.computer = Player("Computer", "O")

    def start_game(self):
        print("Welcome to Tic Tac Toe!")
        self.board.clear_board()
        self.display_board()

        while True:
            self.get_user_move()
            if self.check_winner() or self.check_tie():
                break

            self.get_computer_move()
            if self.check_winner() or self.check_tie():
                break

        self.play_again()

    def display_board(self):
        print("Current Board:")
        self.board.display()

    def get_user_move(self):
        while True:
            position = input("Enter your move (1-9): ")
            if position.isdigit() and 1 <= int(position) <= 9:
                position = int(position)
                if self.board.is_position_empty(position):
                    self.make_move(self.player, position)
                    break
                else:
                    print("That position is already taken. Try again.")
            else:
                print("Invalid input. Try again.")

    def get_computer_move(self):
        position = self.board.get_random_empty_position()
        self.make_move(self.computer, position)

    def make_move(self, player, position):
        self.board.make_move(player, position)
        self.display_board()

    def check_winner(self):
        if self.board.is_winner(self.player):
            print(f"{self.player.get_name()} wins!")
            return True
        elif self.board.is_winner(self.computer):
            print(f"{self.computer.get_name()} wins!")
            return True
        return False

    def check_tie(self):
        if self.board.is_board_full():
            print("It's a tie!")
            return True
        return False

    def play_again(self):
        while True:
            choice = input("Do you want to play again? (y/n): ")
            if choice.lower() == "y":
                self.start_game()
                break
            elif choice.lower() == "n":
                print("Thank you for playing Tic Tac Toe!")
                break
            else:
                print("Invalid input. Try again.")

if __name__ == "__main__":
    game = Game()
    game.start_game()
