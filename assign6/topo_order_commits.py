#!/usr/bin/env python3

import os
import sys
import zlib


ROOT = os.sep
REFS_HEADS = "refs/heads"


class CommitNode:
    """
    Represents a Git commit
    """

    def __init__(self, commit_hash: str):
        self.commit_hash: str = commit_hash
        self.parents: set[CommitNode] = set()
        self.children: set[CommitNode] = set()

    def __str__(self) -> str:
        return self.commit_hash

    def __repr__(self) -> str:
        return (
            f"(commit_hash: {self.commit_hash}, "
            f"parents: {self.parents}, "
            f"children: {self.children})"
        )

    def get_commit_hash(self) -> str:
        """
        Returns the commit hash.
        """

        return self.commit_hash

    def object_path(self) -> str:
        """
        Assumes the current working directory is .git, returns the relative path
        of the object file associated with this commit.
        """

        return f"objects/{self.commit_hash[0:2]}/{self.commit_hash[2:]}"


class GitRepo:
    """
    Does fancy things with a Git repository.
    """

    def __init__(self):
        def get_dot_git() -> str:
            while True:
                if os.path.isdir(".git"):
                    return f"{os.getcwd()}/.git"

                if os.getcwd() == ROOT:
                    print("Not inside a Git repository", file=sys.stderr)
                    sys.exit(1)

                os.chdir("..")

        def get_local_branches() -> list[str]:
            os.chdir(f"{self.dir}/{REFS_HEADS}")
            return os.listdir()

        self.dir: str = get_dot_git()
        self.local_branches: list[str] = get_local_branches()
        self.root_commits: list[CommitNode] = []

    def location(self):
        """
        Directory of git repository.
        """

        return self.dir

    def build_commit_graph(self) -> None:
        """
        Builds commit graph of each local branch.
        """

        def get_head_commits(branches: list[str]) -> list[CommitNode]:
            head_commits: list[CommitNode] = []

            for branch in branches:
                maybe_head_location: str = f"{self.dir}/{REFS_HEADS}/{branch}"

                # Branch name can have "/", causing its commit hash file inside .git
                # to be inside nested directories. For example, for branch name
                # a/b/c the commit hash file is located at .git/refs/heads/a/b/c.
                #
                # Keep traversing down until a file is encountered.
                while not os.path.isfile(maybe_head_location):
                    maybe_head_location = (
                        f"{maybe_head_location}/{os.listdir(maybe_head_location)[0]}"
                    )

                head_location: str = maybe_head_location

                with open(head_location, encoding="UTF-8") as head:
                    head_commits.append(CommitNode(head.read().strip()))

                return head_commits

        def populate_tree(heads: list[CommitNode]) -> list[CommitNode]:
            """
            Uses multiple depth-first searches, each starting from a branch HEAD
            commit. Returns a list of root commits (those with no parents).
            """

            root_commits: list[CommitNode] = []
            existing: dict[CommitNode] = {
                head.get_commit_hash(): head for head in heads
            }

            # Since two branches can have the same head commit, avoid including
            # duplicate commits by constructing from `existing`
            unvisited: list[CommitNode] = list(existing.values())

            while unvisited:
                current: CommitNode = unvisited.pop()

                try:
                    parent_hashes: list[str] = []

                    with open(
                        f"{self.dir}/{current.object_path()}",
                        mode="rb",
                    ) as commit_object:
                        text = zlib.decompress(commit_object.read()).decode().split()

                        for i, token in enumerate(text):
                            if token == "parent":
                                parent_hashes.append(text[i + 1])

                            if token == "author":
                                # Reached end of parent commits metadata, after
                                # which is other metadata and then the commit
                                # message. Since the message could contain "parents"
                                # on one line, which would break parsing, it's best
                                # to exit early.
                                break

                    # `current` has no parents, so it's a leaf node
                    if not parent_hashes:
                        root_commits.append(current)

                    for parent_hash in parent_hashes:
                        parent: CommitNode

                        if parent_hash in existing:
                            parent = existing[parent_hash]
                        else:
                            parent = CommitNode(parent_hash)

                        parent.children.add(current)
                        current.parents.add(parent)

                        unvisited.append(parent)

                except OSError as error:
                    print(
                        f"{os.path.basename(__file__)}: "
                        f"This repository may be using packfiles, which is not supported. "
                        f"Error: {error}",
                        file=sys.stderr,
                    )
                    sys.exit(1)

            return root_commits

        heads: list[CommitNode] = get_head_commits(self.local_branches)

        self.root_commits.extend(populate_tree(heads))

        print(self.root_commits)


if __name__ == "__main__":
    repo = GitRepo()
    print(repo.location())
    repo.build_commit_graph()
