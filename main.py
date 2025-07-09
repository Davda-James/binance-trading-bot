# This file is entry point for cli bot
def entry():
    from src.cli import main as cli_main
    cli_main()

if __name__ == "__main__":
    entry()
