from functools import cached_property

import xxhash


class MetaWalkPath(type):

    @property
    def min(self):
        return self(bytes(self.part_len))

    @property
    def max(self):
        return self(b"".join(
            0b11111111.to_bytes(int(64 / 8), "big")
            for i
            in range(self.part_len)
        ))


class WalkPath(bytes, metaclass=MetaWalkPath):

    part_len: int = int(64 / 8)

    @staticmethod
    def encode_part(part: str):
        return WalkPath(xxhash.xxh3_64_digest(part))

    @classmethod
    def encode(cls, *parts: str):
        return WalkPath(b"".join(
            cls.encode_part(part)
            for part
            in parts
        ))

    @classmethod
    def from_str(cls, walk_path_s: str):
        return WalkPath(bytes.fromhex(walk_path_s))
        # return WalkPath(base64.urlsafe_b64decode(walk_path_s))

    def __str__(self):
        return self.hex()
        # return str(base64.urlsafe_b64encode(self))

    def __repr__(self):
        return "WalkPath.from_str(" + str(self) + ")"

    @cached_property
    def parts(self):
        return tuple(bytes(self)[i:i+self.part_len] for i in range(0, len(bytes(self)), self.part_len))

    def __getitem__(self, key):
        if isinstance(key, int):
            return WalkPath(self.parts[key])
        elif isinstance(key, slice):
            return WalkPath(b"".join(self.parts[key]))
        else:
            raise TypeError(key)

    def __len__(self):
        return len(self.parts)

    def __add__(self, value):
        return WalkPath(super().__add__(value))

    def __radd__(self, value):
        return WalkPath(super().__radd__(value))

    def __le__(self, other):
        return self == other or self < other

    def __ge__(self, other):
        return self == other or self > other

    def __lt__(self, other):
        if not isinstance(other, WalkPath):
            raise TypeError(other)

        min_len = min(len(self), len(other))

        for i in range(min_len):
            if self[i] == other[i]:
                continue
            if bytes(self[i]) > bytes(other[i]):
                return False
            else:
                return True

        if len(self) >= len(other):
            return False

        return True

    def __gt__(self, other):
        if not isinstance(other, WalkPath):
            raise TypeError(other)

        min_len = min(len(self), len(other))

        for i in range(min_len):
            if self[i] == other[i]:
                continue
            if bytes(self[i]) < bytes(other[i]):
                return False
            else:
                return True

        if len(self) <= len(other):
            return False

        return True

    def __contains__(self, key):
        if not isinstance(key, WalkPath):
            raise TypeError(key)

        return len(self) <= len(key) and self.parts == key.parts[0:len(self)]
