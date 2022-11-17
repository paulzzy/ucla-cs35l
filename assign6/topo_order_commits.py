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
        return ", ".join(
            [
                f"commit_hash: {self.commit_hash}",
                # f"parents: {self.parents}",
                # f"children: {self.children}",
            ]
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
        self.branch_heads: dict[str, CommitNode] = {}
        self.commits: list[CommitNode] = []
        self.root_commits: list[CommitNode] = []
        self.topo_sorted_commits: list[CommitNode] = []

        self.__build_commit_graph()
        self.__topo_sort()

    def location(self):
        """
        Directory of git repository.
        """

        return self.dir

    def __build_commit_graph(self) -> None:
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
            dfs_stack: list[CommitNode] = list(existing.values())
            visited: set[CommitNode] = set()

            while dfs_stack:
                current: CommitNode = dfs_stack.pop()

                if current in visited:
                    continue

                visited.add(current)
                self.commits.append(current)

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

                        dfs_stack.append(parent)

                except OSError as error:
                    print(
                        f"{os.path.basename(__file__)}: "
                        f"This repository may be using packfiles, which is not supported"
                        f": {error}",
                        file=sys.stderr,
                    )
                    sys.exit(1)

            return root_commits

        heads: list[CommitNode] = get_head_commits(self.local_branches)

        for (head, branch) in zip(heads, self.local_branches):
            self.branch_heads.setdefault(head.commit_hash, []).append(branch)

        self.root_commits.extend(populate_tree(heads))

    def __topo_sort(self) -> None:
        """
        Generates a topological ordering of the commit graph.
        """

        num_parents: dict[CommitNode] = {
            commit: len(commit.children) for commit in self.commits
        }

        dfs_queue: list[CommitNode] = [
            commit for commit in self.commits if num_parents[commit] == 0
        ]

        while dfs_queue:
            current = dfs_queue.pop(0)

            for child in sorted(current.parents, key=lambda child: child.commit_hash):
                num_parents[child] -= 1
                if num_parents[child] == 0:
                    dfs_queue.append(child)

            self.topo_sorted_commits.append(current)

    def __str__(self) -> str:
        """
        Converts topologically sorted commit graph to formatted string.
        """

        output: list[str] = []
        prev: CommitNode = CommitNode("")

        for commit in self.topo_sorted_commits:
            current_line: str = f"{commit.commit_hash}"

            # When current commit is not a parent of the previous, add a "sticky
            # end" and "sticky start" to indicate how to reconstruct the commit
            # graph. The sticky parts include information on the previous
            # commit's parents and the current commit's children.
            #
            # Format of sticky end:
            # ```
            # parent_1 parent_2 ... parent_n=
            # ```
            #
            # Format of sticky start:
            # ```
            #
            # =child_1 child_2 ... child_n
            # ```
            if prev not in commit.children and len(commit.children) > 0:
                sticky_end: str = (
                    f"{' '.join([parent.commit_hash for parent in prev.parents])}="
                )
                sticky_start: str = (
                    f"\n\n="
                    f"{' '.join([child.commit_hash for child in commit.children])}\n"
                )
                current_line = f"{sticky_end}{sticky_start}{current_line}"

            if commit.commit_hash in self.branch_heads:
                branch_names = sorted(
                    self.branch_heads[commit.commit_hash], key=lambda branch: branch
                )
                current_line = f"{current_line} {' '.join(branch_names)}"

            output.append(current_line)

            prev = commit

        return "\n".join(output)


def topo_order_commits():
    """
    Used by instructor-provided test suite.
    """

    repo = GitRepo()
    print(repo)


if __name__ == "__main__":
    topo_order_commits()
