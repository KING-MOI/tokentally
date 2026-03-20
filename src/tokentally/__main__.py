import os
import sys

from tokentally.cli import main


def run() -> int:
    try:
        return main()
    except KeyboardInterrupt:
        return 130
    except BrokenPipeError:
        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, sys.stdout.fileno())
        return 141


if __name__ == "__main__":
    raise SystemExit(run())
