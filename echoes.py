import argparse


def echo(message: str, times: int) -> None:
    """Prints a message multiple times."""
    for _ in range(times):
        print(message)


def main() -> None:
    parser = argparse.ArgumentParser(description="Repeat a message multiple times")
    parser.add_argument("message", help="Message to repeat")
    parser.add_argument("-n", "--times", type=int, default=1, help="Number of repetitions")
    args = parser.parse_args()
    echo(args.message, args.times)


if __name__ == "__main__":
    main()
