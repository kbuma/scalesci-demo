Based on the requirements, here are the core classes, functions, and methods that will be necessary for the Tic Tac Toe game:

1. Game:
   - `start_game()`: Starts the game and manages the game flow.
   - `display_board()`: Displays the current state of the game board.
   - `get_user_move()`: Prompts the user for their move and validates it.
   - `get_computer_move()`: Generates the computer's move.
   - `make_move(player, position)`: Updates the game board with the player's move.
   - `check_winner()`: Checks if there is a winner.
   - `check_tie()`: Checks if the game is a tie.
   - `play_again()`: Asks the user if they want to play again.

2. Board:
   - `__init__(self)`: Initializes the game board.
   - `is_position_empty(self, position)`: Checks if a position on the board is empty.
   - `is_board_full(self)`: Checks if the board is full.
   - `make_move(self, player, position)`: Updates the board with the player's move.
   - `is_winner(self, player)`: Checks if the player has won.

3. Player:
   - `__init__(self, name, symbol)`: Initializes a player with a name and symbol.
   - `get_name(self)`: Returns the name of the player.
   - `get_symbol(self)`: Returns the symbol of the player.

Now, let's proceed with creating the necessary files and implementing the code.

**game.py**
