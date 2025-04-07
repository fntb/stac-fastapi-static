import pytest

from stac_fastapi.static.core import WalkPath


class TestWalkPath():

    def test_min_max(self):
        assert isinstance(WalkPath.min, WalkPath)
        assert isinstance(WalkPath.max, WalkPath)

    def test_encoding(self):
        parts = ["Hello", ",", "World", "!", "\n", "This is a test."]

        for part in parts:
            assert len(bytes(WalkPath.encode_part(part))) == WalkPath.part_len

        assert len(bytes(WalkPath.encode(*parts))
                   ) == WalkPath.part_len * len(parts)

    def test_list(self):
        parts = ["Hello", ",", "World", "!"]
        encoded_parts = [
            WalkPath.encode_part(part)
            for part
            in parts
        ]

        walk_path = WalkPath.encode(*parts)

        assert len(walk_path) == len(parts)
        assert list(walk_path.parts) == encoded_parts

        for i in range(len(encoded_parts)):
            assert encoded_parts[i] == walk_path[i]

    def test_comparisons(self):
        a_parts = ["Hello", ",", "World", "1", "!"]
        a_child_parts = ["Hello", ",", "World", "1", "!", "This is a child"]
        b_parts = ["Hello", ",", "World", "2", "!"]

        a_walk_path = WalkPath.encode(*a_parts)
        a_child_walk_path = WalkPath.encode(*a_child_parts)
        b_walk_path = WalkPath.encode(*b_parts)

        assert a_child_walk_path >= a_walk_path
        assert a_child_walk_path > a_walk_path
        assert a_child_walk_path != a_walk_path
        assert not a_child_walk_path == a_walk_path
        assert not a_child_walk_path <= a_walk_path
        assert not a_child_walk_path < a_walk_path
        assert a_child_walk_path in a_walk_path

        assert a_walk_path >= a_walk_path
        assert not a_walk_path > a_walk_path
        assert not a_walk_path != a_walk_path
        assert a_walk_path == a_walk_path
        assert a_walk_path <= a_walk_path
        assert not a_walk_path < a_walk_path
        assert a_walk_path in a_walk_path

        assert b_walk_path >= a_walk_path
        assert b_walk_path > a_walk_path
        assert b_walk_path != a_walk_path
        assert not b_walk_path == a_walk_path
        assert not b_walk_path <= a_walk_path
        assert not b_walk_path < a_walk_path
        assert not b_walk_path in a_walk_path
