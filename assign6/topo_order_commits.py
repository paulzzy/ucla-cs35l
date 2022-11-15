#!/usr/bin/env python3

import os
import sys


class GitRepo:
    """
    Does fancy things with a git repository.
    """

    def __init__(self):
        """
        Initialize by finding .git directory in current or higher directories. Exits if none found.
        """

        root = os.sep
        self.dir = root

        while True:
            if os.path.isdir(".git"):
                self.dir = f"{os.getcwd()}/.git"
                return

            if os.getcwd() == root:
                print("Not inside a Git repository", file=sys.stderr)
                sys.exit(1)

            try:
                os.chdir("..")
            except OSError as error:
                print(f"bruh something went wrong: {error}")

    def location(self):
        """
        Directory of git repository.
        """

        return self.dir

    def local_branches(self) -> list[str]:
        """
        Branches on the local computer.
        """

        os.chdir(f"{self.dir}/refs/heads")

        return os.listdir()


if __name__ == "__main__":
    repo = GitRepo()
    print(repo.location())
    print(repo.local_branches())
