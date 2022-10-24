"""
My linter got mad at me for not having docstrings lmao so might as well
"""
#!/usr/bin/env python3

import argparse
import math
import random
import sys


class Shuffer:
    """
    My linter got mad at me for not having docstrings lmao so might as well
    """

    def __init__(
        self,
        head_count: int,
        repeat: bool,
    ) -> None:
        self.lines: list[str] = []
        self.head_count = head_count if head_count else math.inf
        self.repeat = repeat

    def use(self, lines: list[str]) -> None:
        """
        My linter got mad at me for not having docstrings lmao so might as well
        """
        self.lines = lines

    def out(self) -> None:
        """
        My linter got mad at me for not having docstrings lmao so might as well
        """
        while True:
            random.shuffle(self.lines)

            count = 0
            for line in self.lines:
                if self.repeat:
                    print(random.choice(self.lines))
                else:
                    print(line)

                count += 1
                if count >= self.head_count:
                    break

            if not self.repeat or self.head_count < math.inf:
                break


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Write a random permutation of the input lines to standard output."
    )

    group = parser.add_mutually_exclusive_group()
    group.add_argument("-e", "--echo", action="store_true")
    group.add_argument("-i", "--input-range", type=str)
    parser.add_argument("-n", "--head-count", type=int)
    parser.add_argument("-r", "--repeat", action="store_true")
    parser.add_argument("arg", nargs="*")

    args, unknown = parser.parse_known_args()

    LO = 0
    HI = 0

    # Validate input_range format
    if args.input_range:
        possible_range = args.input_range.split("-")

        if len(possible_range) != 2:
            parser.error(f"invalid input range {args.input_range}")

        try:
            LO = int(possible_range[0])
            HI = int(possible_range[1])
        except ValueError:
            parser.error(f"invalid input range {args.input_range}")

        if args.arg:
            parser.error(f"extra operand '{args.arg[0]}'")

    shuffer = Shuffer(args.head_count, args.repeat)

    match (args.arg, args.echo, args.input_range is not None):
        # -e flag is passed
        case (arg, True, input_range):
            shuffer.use(arg + unknown)
        # -i flag is passed
        case (arg, False, True):
            shuffer.use(list(range(LO, HI + 1)))
        # Read from stdin
        case ([], False, False) | (["-"], False, False):
            shuffer.use(sys.stdin.read().splitlines())
        # Read from file
        case ([filename], False, False):
            with open(filename, encoding="UTF-8") as file:
                shuffer.use(file.read().splitlines())
        case _:
            parser.error(f"extra operand: '{args.arg[1]}'")

    shuffer.out()
