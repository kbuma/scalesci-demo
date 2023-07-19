   # Check if Python is already installed
   python3 --version

   # If Python is not installed, install it
   # For macOS or Linux
   brew install python3

   # For Windows
   choco install python
   
   # Create a virtual environment
   python3 -m venv env

   # Activate the virtual environment
   source env/bin/activate
   
   # Install the dependencies using pip
   pip install -r requirements.txt
   
   # Run the game.py file
   python game.py
   