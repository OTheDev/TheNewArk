###############################################################################
#   Imports.
###############################################################################
from collections.abc import Sequence
from random import shuffle
from typing import List, Tuple


###############################################################################
#   Constants.
###############################################################################
N_TONEROW = 12  # Number of elements in a tone row.

valid_values = set(range(N_TONEROW))

chromatic_scale = (
    # 0    1     2    3     4    5    6     7    8     9    10    11
    "C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"
    )


###############################################################################
#   Exceptions.
###############################################################################
class ToneRowException(Exception):
    pass


###############################################################################
#   ToneRow class.
###############################################################################
class ToneRow:
    _valid_values = set(range(N_TONEROW))
    _chromatic_scale = (
        # 0    1     2    3     4    5    6     7    8     9    10    11
        "C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"
        )

    def __init__(self, tonerow: Sequence[int]):
        """Initializer"""
        if isinstance(tonerow, tuple) or isinstance(tonerow, list):
            self._tonerow = tonerow
        else:
            self._tonerow = tuple(tonerow)

        if not ToneRow._is_tonerow(self.tonerow):
            raise ToneRowException("A 12-element sequence of unique ints in "
                                   "[0, 11] is required.")

    @classmethod
    def random(cls) -> List[int]:
        """Alternate constructor. A random tone row is generated."""
        result = list(range(N_TONEROW))
        shuffle(result)
        return cls(result)

    @property
    def tonerow(self):
        return self._tonerow

    @staticmethod
    def _is_tonerow(tr: Sequence[int]) -> bool:
        """Returns True if `tonerow` is a valid tone row. Otherwise, returns
        False. A tone row is considered valid iff it is a 12-element sequence
        of unique ints in [0, 11]."""
        tr = set(tr)  # Keep only unique elements.

        if len(tr) != 12:
            return False

        flag = True
        for x in tr:
            if x not in ToneRow._valid_values:
                flag = False
                break

        return True if flag else False

    @staticmethod
    def print(tonerow) -> None:
        if isinstance(tonerow, ToneRow):
            print(tonerow)
            return
        assert(ToneRow._is_tonerow(tonerow))
        s = " ".join(
            format(ToneRow._chromatic_scale[x], "<2") for x in tonerow)
        print(s)

    def __repr__(self) -> str:
        return "(" + ", ".join(repr(x) for x in self.tonerow) + ")"

    def __str__(self) -> str:
        return " ".join(
            format(ToneRow._chromatic_scale[x], "<2") for x in self.tonerow)

    def inversion(self) -> Tuple[int]:
        """Returns the inversion of the tone row.
        Let P be a sequence representing the tone row. Its inversion is the
        sequence, I, such that
            I[0] = P[0],
            I[i] = (12 - (P[i] - P[0]) + P[0]) mod 12."""
        iterator = iter(self.tonerow)
        f = next(iterator)
        return (f,) + tuple(
            (N_TONEROW - (x - f) + f) % N_TONEROW for x in iterator)

    def retrograde(self) -> Tuple[int]:
        """Returns the retrograde of the tone row."""
        return tuple(reversed(self.tonerow))

    def retrograde_inversion(self) -> Tuple[int]:
        """Returns the retrograde-inversion of the tone row."""
        return tuple(reversed(self.inversion()))

    def variations(self) -> Tuple[Tuple[int]]:
        """Returns the retrograde, inversion, and retrograde-inversion of the
        tone row as a 3-element tuple of tuples of ints."""
        inv = self.inversion()
        return tuple(reversed(self.tonerow)), inv, tuple(reversed(inv))

    def twelve_tone_matrix(self) -> List[List[int]]:
        """Returns the corresponding twelve tone matrix of the tone row,
        implemented as a list of lists of integers. Based on a C implementation
        at https://github.com/mmuldo/12-tone."""
        iterator = iter(self.tonerow)
        first = next(iterator)
        result = []
        for x in self.tonerow:
            temp = []
            if x < first:
                interval = x - first
            else:
                interval = x - first - N_TONEROW
            for y in self.tonerow:
                temp.append((y - interval) % N_TONEROW)
            result.append(temp)

        return result

    def print_twelve_tone_matrix(self) -> None:
        """Prints the twelve tone matrix of the tone row."""
        temp = [0] * N_TONEROW
        for i in range(N_TONEROW):
            if self.tonerow[i] < self.tonerow[0]:
                interval = self.tonerow[i] - self.tonerow[0]
            else:
                interval = self.tonerow[i] - self.tonerow[0] - N_TONEROW

            for j in range(N_TONEROW):
                temp[j] = (self.tonerow[j] - interval) % N_TONEROW

            print(f"P{(-interval) % N_TONEROW:<2} | ", end="")
            ToneRow.print(temp)


###############################################################################
#   Functions. Assume that a tone row is represented by a 12-element sequence
#              of unique integers in [0, 11].
###############################################################################
def retrograde(tr: Sequence[int]) -> Tuple[int]:
    """Returns the retrograde of the tone row."""
    return tuple(reversed(tr))


def inversion(tr: Sequence[int]) -> Tuple[int]:
    """Returns the inversion of the tone row.

    Let P be a sequence representing the tone row. Its inversion is the
    sequence, I, such that
        I[0] = P[0],
        I[i] = (12 - (P[i] - P[0]) + P[0]) mod 12.

    See, for example, "The Mathematics of Twelve Tone Music" by Bethany
    Shears, which also provides a mathematical definition of the Twelve Tone
    Matrix."""
    it = iter(tr)
    f = next(it)
    return (f,) + tuple((N_TONEROW - (x - f) + f) % N_TONEROW for x in it)


def retrograde_inversion(tr: Sequence[int]) -> Tuple[int]:
    """Returns the retrograde-inversion of the tone row."""
    it = reversed(tr)
    f = next(it)
    return (f,) + tuple((N_TONEROW - (x - f) + f) % N_TONEROW for x in it)


def variations(tr: Sequence[int]) -> Tuple[Tuple[int]]:
    """Returns the retrograde, inversion, and retrograde-inversion of the tone
    row."""
    inv = inversion(tr)
    return tuple(reversed(tr)), inv, tuple(reversed(inv))


def twelve_tone_matrix(tr: Sequence[int]) -> List[List[int]]:
    """Given a 12-element sequence of unique integers in [0, 11] representing
    a tone row, return its corresponding twelve tone matrix implemented as a
    list of lists of integers.

    Based on a C implementation at https://github.com/mmuldo/12-tone."""
    result = []
    for i in range(12):
        temp = []

        if tr[i] < tr[0]:
            interval = tr[i] - tr[0]
        else:
            interval = tr[i] - tr[0] - 12

        for j in range(12):
            temp.append((tr[j] - interval) % 12)
        result.append(temp)

    return result


def print_tonerow(tr: Sequence[int]) -> None:
    """Prints the tone row using note names rather than integers."""
    for note in tr:
        print(f"{chromatic_scale[note]:<2} ", end="")
    print()


def print_twelve_tone_matrix(tr: Sequence[int]) -> None:
    """Prints the corresponding twelve tone matrix of the tone row using note
    names rather than integers."""
    temp = [0] * 12
    for i in range(12):
        if tr[i] < tr[0]:
            interval = tr[i] - tr[0]
        else:
            interval = tr[i] - tr[0] - 12

        for j in range(12):
            temp[j] = (tr[j] - interval) % 12

        print(f"P{(-interval) % 12:<2} | ", end="")
        print_tonerow(temp)


def print_variations(tr: Sequence[int]) -> None:
    r, i, ri = variations(tr)
    for a, b in zip(("P0", "R0", "I0", "RI0"), (tr, r, i, ri)):
        print(f"{a:<3}: ", end="")
        print_tonerow(b)


def is_tonerow(tr):
    """Returns True if `tr` is a valid tone row. Otherwise, returns
    False. A tone row is considered valid iff it is a 12-element tuple
    of unique ints in [0, 11]."""
    if not isinstance(tr, tuple):
        return False
    tr = set(tr)       # Keep only unique values
    if len(tr) != 12:  # Tone row must consist of 12 unique values.
        return False
    # All 12 values must be integers in [0, 11].
    return all(x in valid_values for x in tr)


###############################################################################
#   Private helpers.
###############################################################################
def _random() -> List[int]:
    """Returns a randomly-generated tone row."""
    result = list(range(N_TONEROW))
    shuffle(result)
    return result


def _transpose_2d_matrix(a: List[list]) -> List[list]:
    """Given a 2D matrix `a` implemented as a list of lists, returns the
    transpose of the matrix as a list of lists."""
    return [list(j) for j in zip(*a)]
