"""Start the Movie Manager.

    python main.py          -> opens the graphical interface
    python main.py --cli    -> runs the text menu in the terminal
"""

import sys

if __name__ == "__main__":
    if "--cli" in sys.argv:
        from movie_manager.cli import main
    else:
        from movie_manager.gui import main
    main()
