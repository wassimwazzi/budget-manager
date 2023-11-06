import sys
import getopt
import dotenv


def set_env():
    opts, args = getopt.getopt(sys.argv[1:], "p", ["prod"])
    if not opts:
        print("Running in development mode")
        dotenv.load_dotenv(dotenv_path=".env.dev", override=True)
    for opt, arg in opts:
        if opt in ("-p", "--prod"):
            print("Running in production mode")
            dotenv.load_dotenv(dotenv_path=(".env.prod"), override=True)
        else:
            print("Unrecognized option. Running in development mode")
            dotenv.load_dotenv(dotenv_path=(".env.prod"), override=True)


if __name__ == "__main__":
    set_env()
    from src.app import run

    run()
