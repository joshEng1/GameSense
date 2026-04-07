from search_engine import SearchEngine
from ui import GameUI


def main():
    engine = SearchEngine()
    app = GameUI(engine)
    app.run()


if __name__ == "__main__":
    main()