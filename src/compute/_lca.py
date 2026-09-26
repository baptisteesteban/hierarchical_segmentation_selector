from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class _BlockKind:
    length: int
    signature: int


class LCA:
    """Lowest common ancestor index with O(1) queries after preprocessing."""

    def __init__(self, parents: list[int]):
        self._parents = parents.copy()
        self._num_nodes = len(parents)

        if self._num_nodes == 0:
            raise ValueError("Parent table must contain at least one node")

        self._root = self._validate_and_find_root(self._parents)
        self._children = self._build_children(self._parents)
        self._depth = self._build_depth(self._children, self._root)

        (
            self._euler_nodes,
            self._euler_depths,
            self._first_occurrence,
        ) = self._build_euler_tour(self._children, self._depth, self._root)

        self._build_rmq_index()

    @property
    def root(self) -> int:
        return self._root

    @property
    def children(self) -> list[list[int]]:
        return [child.copy() for child in self._children]

    @property
    def num_nodes(self) -> int:
        return self._num_nodes

    def is_ancestor(self, ancestor: int, node: int) -> bool:
        if not self._is_valid_node(ancestor) or not self._is_valid_node(node):
            raise ValueError("Node index out of bounds")
        return self(ancestor, node) == ancestor

    def __call__(self, u: int, v: int) -> int:
        if not self._is_valid_node(u) or not self._is_valid_node(v):
            raise ValueError("Node index out of bounds")

        left = self._first_occurrence[u]
        right = self._first_occurrence[v]
        if left > right:
            left, right = right, left

        euler_idx = self._rmq_query(left, right)
        return self._euler_nodes[euler_idx]

    def _is_valid_node(self, node: int) -> bool:
        return 0 <= node < self._num_nodes

    @staticmethod
    def _validate_and_find_root(parents: list[int]) -> int:
        num_nodes = len(parents)
        roots: list[int] = []

        for node, parent in enumerate(parents):
            if parent == -1:
                roots.append(node)
                continue
            if parent < 0 or parent >= num_nodes:
                raise ValueError(f"Invalid parent index at node {node}: {parent}")
            if parent == node:
                raise ValueError(f"Node {node} cannot be its own parent")

        if len(roots) != 1:
            raise ValueError("Parent table must contain exactly one root")

        state = [0] * num_nodes
        for node in range(num_nodes):
            if state[node] != 0:
                continue

            path: list[int] = []
            current = node
            while current != -1 and state[current] == 0:
                state[current] = 1
                path.append(current)
                current = parents[current]

            if current != -1 and state[current] == 1:
                raise ValueError("Parent table contains a cycle")

            for visited_node in path:
                state[visited_node] = 2

        return roots[0]

    @staticmethod
    def _build_children(parents: list[int]) -> list[list[int]]:
        children: list[list[int]] = [[] for _ in range(len(parents))]
        for node, parent in enumerate(parents):
            if parent != -1:
                children[parent].append(node)
        return children

    @staticmethod
    def _build_depth(children: list[list[int]], root: int) -> list[int]:
        depth = [-1] * len(children)
        stack: list[tuple[int, int]] = [(root, 0)]

        while stack:
            node, node_depth = stack.pop()
            if depth[node] != -1:
                continue
            depth[node] = node_depth
            for child in children[node]:
                stack.append((child, node_depth + 1))

        if any(node_depth < 0 for node_depth in depth):
            raise ValueError("Parent table is disconnected from the root")

        return depth

    @staticmethod
    def _build_euler_tour(
        children: list[list[int]], depth: list[int], root: int
    ) -> tuple[list[int], list[int], list[int]]:
        euler_nodes: list[int] = [root]
        euler_depths: list[int] = [depth[root]]
        first_occurrence: list[int] = [-1] * len(children)
        first_occurrence[root] = 0

        # Stack entries: (node, next_child_index)
        stack: list[tuple[int, int]] = [(root, 0)]

        while stack:
            node, child_idx = stack[-1]
            node_children = children[node]

            if child_idx < len(node_children):
                child = node_children[child_idx]
                stack[-1] = (node, child_idx + 1)
                stack.append((child, 0))

                euler_nodes.append(child)
                euler_depths.append(depth[child])
                if first_occurrence[child] == -1:
                    first_occurrence[child] = len(euler_nodes) - 1
            else:
                stack.pop()
                if stack:
                    parent = stack[-1][0]
                    euler_nodes.append(parent)
                    euler_depths.append(depth[parent])

        return euler_nodes, euler_depths, first_occurrence

    @staticmethod
    def _block_signature(depths: list[int], start: int, end: int) -> int:
        signature = 0
        for idx in range(start + 1, end):
            delta = depths[idx] - depths[idx - 1]
            if delta not in (1, -1):
                raise ValueError(
                    "Euler depth array is not +/-1 between consecutive entries"
                )
            signature = (signature << 1) | (1 if delta == 1 else 0)
        return signature

    @staticmethod
    def _build_micro_table(block_kind: _BlockKind) -> list[int]:
        length = block_kind.length
        if length <= 0:
            raise ValueError("Block length must be positive")

        relative_depths = [0] * length
        signature = block_kind.signature
        for idx in range(1, length):
            bit_pos = length - 1 - idx
            step_is_plus = (signature >> bit_pos) & 1
            relative_depths[idx] = relative_depths[idx - 1] + (
                1 if step_is_plus else -1
            )

        # Flattened upper-triangular table using full matrix indexing.
        table = [0] * (length * length)
        for left in range(length):
            best = left
            table[left * length + left] = left
            for right in range(left + 1, length):
                if relative_depths[right] < relative_depths[best]:
                    best = right
                table[left * length + right] = best

        return table

    @staticmethod
    def _recommended_block_size(length: int) -> int:
        if length <= 1:
            return 1
        # Half-log block size keeps micro-table universe sublinear.
        return max(1, (length.bit_length() - 1) // 2)

    def _build_rmq_index(self) -> None:
        m = len(self._euler_depths)
        self._block_size = self._recommended_block_size(m)
        self._num_blocks = (m + self._block_size - 1) // self._block_size

        self._block_starts = [
            block * self._block_size for block in range(self._num_blocks)
        ]
        self._block_lengths = [
            min(self._block_size, m - start) for start in self._block_starts
        ]

        self._micro_tables: dict[_BlockKind, list[int]] = {}
        self._block_kinds: list[_BlockKind] = []
        self._block_min_euler_idx: list[int] = []

        for block in range(self._num_blocks):
            start = self._block_starts[block]
            block_len = self._block_lengths[block]
            end = start + block_len

            kind = _BlockKind(
                length=block_len,
                signature=self._block_signature(self._euler_depths, start, end),
            )
            self._block_kinds.append(kind)

            if kind not in self._micro_tables:
                self._micro_tables[kind] = self._build_micro_table(kind)

            self._block_min_euler_idx.append(self._query_block(block, 0, block_len - 1))

        self._build_sparse_table_over_blocks()

    def _build_sparse_table_over_blocks(self) -> None:
        if self._num_blocks == 0:
            self._sparse_table = []
            self._block_logs = [0]
            return

        max_k = self._num_blocks.bit_length()
        self._sparse_table: list[list[int]] = [self._block_min_euler_idx.copy()]

        for level in range(1, max_k):
            prev = self._sparse_table[level - 1]
            interval = 1 << level
            half = interval >> 1
            size = self._num_blocks - interval + 1
            if size <= 0:
                break

            cur: list[int] = [0] * size
            for idx in range(size):
                left = prev[idx]
                right = prev[idx + half]
                cur[idx] = self._min_euler_index(left, right)
            self._sparse_table.append(cur)

        self._block_logs = [0] * (self._num_blocks + 1)
        for length in range(2, self._num_blocks + 1):
            self._block_logs[length] = self._block_logs[length // 2] + 1

    def _query_block(self, block: int, local_left: int, local_right: int) -> int:
        if local_left > local_right:
            local_left, local_right = local_right, local_left

        block_len = self._block_lengths[block]
        if local_left < 0 or local_right >= block_len:
            raise ValueError("Local block interval out of bounds")

        kind = self._block_kinds[block]
        table = self._micro_tables[kind]
        local_min = table[local_left * block_len + local_right]
        return self._block_starts[block] + local_min

    def _query_blocks(self, left_block: int, right_block: int) -> int:
        if left_block > right_block:
            raise ValueError("Invalid block range")

        span = right_block - left_block + 1
        level = self._block_logs[span]
        left_idx = self._sparse_table[level][left_block]
        right_idx = self._sparse_table[level][right_block - (1 << level) + 1]
        return self._min_euler_index(left_idx, right_idx)

    def _min_euler_index(self, left_idx: int, right_idx: int) -> int:
        left_depth = self._euler_depths[left_idx]
        right_depth = self._euler_depths[right_idx]
        if left_depth < right_depth:
            return left_idx
        if right_depth < left_depth:
            return right_idx
        return left_idx if left_idx <= right_idx else right_idx

    def _rmq_query(self, left: int, right: int) -> int:
        if left < 0 or right >= len(self._euler_depths):
            raise ValueError("Euler interval out of bounds")
        if left > right:
            left, right = right, left

        left_block = left // self._block_size
        right_block = right // self._block_size

        if left_block == right_block:
            return self._query_block(
                left_block, left % self._block_size, right % self._block_size
            )

        candidates: list[int] = []

        left_start = self._block_starts[left_block]
        left_len = self._block_lengths[left_block]
        candidates.append(
            self._query_block(left_block, left - left_start, left_len - 1)
        )

        right_start = self._block_starts[right_block]
        candidates.append(self._query_block(right_block, 0, right - right_start))

        middle_left = left_block + 1
        middle_right = right_block - 1
        if middle_left <= middle_right:
            candidates.append(self._query_blocks(middle_left, middle_right))

        best = candidates[0]
        for candidate in candidates[1:]:
            best = self._min_euler_index(best, candidate)
        return best
