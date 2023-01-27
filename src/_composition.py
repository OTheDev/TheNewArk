###############################################################################
#   Imports
###############################################################################
import os
import time

import numpy as np

from itertools import chain
from random import choice, randint, randrange, shuffle
from time import perf_counter

from _midiout import MidiOut
from _midi_constants import MAX_VELOCITY, MIDI_NOTE_NAMES, MIN_VELOCITY,      \
                            NOTE_OFF, NOTE_ON, N_PITCHES, N_PKEYS
from _serial import Serial
from _tonerow import N_TONEROW, variations, _random


###############################################################################
#   Logging
###############################################################################
import logging
logger = logging.getLogger()


###############################################################################
#   Global Constants
#
#   map_0to87_to_0to127 : maps piano key indices to MIDI note numbers. The
#                         integers in [21, 108] are MIDI note numbers
#                         corresponding to piano keys.
#
#   map_0to11_to_0to87  : maps pitch classes to piano key indices.
#
#   map_0to87_to_0to11  : maps piano key indices to pitch classes.
#
#   map_0to127_to_0to11 : maps MIDI note numbers to pitch classes. Only MIDI
#                         note numbers [21, 108] (i.e. piano keys) are
#                         initialized.
#
#   midiout             : shared `MidiOut` instance.
#
#   ser                 : shared `Serial` instance. Finds and opens a
#                         serial port. Read timeout is 4.8 seconds and
#                         writing attempts to write all message bytes but
#                         does not try again (returns immediately). One
#                         drone iteration is 4.800 seconds.
###############################################################################
map_0to87_to_0to127 = np.array(range(21, 109), dtype=np.uint8)

map_0to11_to_0to87 = {}
for i in range(N_TONEROW):
    map_0to11_to_0to87[i] = tuple(
        i for i in range((i + 3) % N_TONEROW, N_PKEYS, N_TONEROW))

map_0to87_to_0to11 = np.empty(N_PKEYS, dtype=np.uint8)
map_0to87_to_0to11[0] = 9   # A0
map_0to87_to_0to11[1] = 10  # A#0/Bb0
map_0to87_to_0to11[2] = 11  # B0 (C1 next)
for i in range(N_PKEYS - 3):
    map_0to87_to_0to11[i + 3] = i % N_TONEROW

map_0to127_to_0to11 = np.empty(N_PITCHES, dtype=np.uint8)
map_0to127_to_0to11[21] = 9
map_0to127_to_0to11[22] = 10
map_0to127_to_0to11[23] = 11
for i in range(N_PKEYS - 3):
    map_0to127_to_0to11[24 + i] = i % N_TONEROW

midiout = MidiOut()

ser = Serial(baudrate=57_600, timeout=10, write_timeout=0)


###############################################################################
#   Handlers
###############################################################################
def restart_computer():
    pwd = os.environ["TNAPWD"]
    os.system(f"echo {pwd} | sudo -S shutdown -r now")


###############################################################################
#   Composition class
###############################################################################
class Composition:
    midiout = midiout                                   # MidiOut instance
    ser = ser                                           # Serial instance
    channel = 0                                         # Default channel
    velocity = int((MIN_VELOCITY + MAX_VELOCITY) / 2)   # Default velocity
    bpm = 102                                           # Default bpm
    timer = perf_counter                                # Timer

    # Records time at which last composition was played.
    time_lastPlayed = timer()

    def __init__(self, tonerow, bpm, ID=-1):
        """Default initializer."""
        self.tonerow = tonerow
        self.bpm = bpm
        self.id = ID

        # Possible durations for end-of-variation (eov), end-of-composition
        # (eoc), and otherwise (o). Drawing an eighth or triplet-eighth note
        # means the next note is an eighth note or the next two notes are
        # triplet-eighth notes.
        self.dur_eov = (120 / bpm,  # Half note
                        60 / bpm)   # Quarter note
        self.dur_eoc = 240 / bpm    # Whole note
        self.dur_o = (
            60 / bpm,               # Quarter note
            30 / bpm,               # Eighth note
            20 / bpm)               # Triplet-eighth note

        # Payload.
        self.payload = {
            "id": self.id,          # Composition/user number
            "notes": None,          # MIDI note numbers
            "durations": None       # Durations of notes
        }

        self._gen_comp()

    @classmethod
    def from_nobpm(cls, notes, durations, ID=-1):
        """
        Alternate constructor. A composition can be defined by the notes
        that are played as well as their corresponding durations.
        """
        obj = cls.__new__(cls)  # Does not call __init__.

        obj.notes = notes
        obj.durations = durations
        obj.id = ID

        obj.payload = {
            "id": obj.id,
            "notes": obj.notes,
            "durations": obj.durations
        }

        return obj

    @classmethod
    def from_random(cls, bpm=None):
        """Alternate constructor. Generates a random `Composition` instance."""
        if bpm is None:
            bpm = cls.bpm
        return cls(tonerow=_random(), bpm=bpm)

    @staticmethod
    def randomize_octaves(row):
        """Randomize octaves, exclude 7th and 8th octaves."""
        return (choice(map_0to11_to_0to87[x][0:-1]) if
                len(map_0to11_to_0to87[x]) == 7 else
                choice(map_0to11_to_0to87[x][0:-2]) for x in row)

    def _gen_comp(self):
        # Create `self.notes`.
        self._gen_notes()
        # Create `self.durations`.
        self._gen_durations()
        self.payload["notes"] = self.notes
        self.payload["durations"] = self.durations

    def _gen_notes(self):
        """Creates a 48-element list of MIDI note numbers, `self.notes`."""
        rows = [self.randomize_octaves(v) for v in variations(self.tonerow)]
        shuffle(rows)
        self.notes = list(map(lambda x: map_0to87_to_0to127[x],
                              chain(self.randomize_octaves(self.tonerow),
                                    *rows)))
        # First and last note will be constrained to a lower octave.
        self.notes[0] = map_0to87_to_0to127[choice(
            map_0to11_to_0to87[map_0to127_to_0to11[self.notes[0]]][1:-3])]
        self.notes[-1] = map_0to87_to_0to127[choice(
            map_0to11_to_0to87[map_0to127_to_0to11[self.notes[-1]]][1:-3])]

    def _gen_durations(self):
        """Creates a 48-element list of note durations `self.durations`."""
        self.durations = []
        n = len(self.tonerow)        # Length of a tone row.
        for i in range(4):           # Four tone rows in a composition.
            cur = 0                  # Current position in tone row.
            while cur < n:
                remaining = n - cur  # Notes remaining in tone row.
                if remaining == 1:   # One note remaining in tone row.
                    break

                # Make first note of composition a quarter or eighth note.
                if i == 0 and cur == 0:
                    notes_per_beat = 1 if randrange(2) else 2
                else:
                    notes_per_beat = randint(
                        1, min(remaining - 1, len(self.dur_o)))

                for j in range(notes_per_beat):
                    self.durations.append(self.dur_o[notes_per_beat - 1])
                    cur += 1

            # Last note is a long note.
            if i == 3:
                # Whole note for last note of a composition.
                self.durations.append(self.dur_eoc)
            else:
                # Quarter or half note for last note of a variation.
                self.durations.append(choice(self.dur_eov))

    def play(self):
        for note, duration in zip(self.notes, self.durations):
            logger.info(f"({MIDI_NOTE_NAMES[note]:7},"
                        f" {duration:.3})")

            # Send serial message to output lights.
            message = self.serial_message_builder(note, duration)
            n = self.ser.write(message)
            if n < len(message):
                logger.critical("Not all bytes written through USB-Serial. "
                                "Restarting.")
                restart_computer()

            # Receive a response from microcontroller or restart otherwise.
            self.receive_response()

            # Play `note` for duration `duration`.
            self.__class__.midiout.send_message(
                (NOTE_ON + self.channel, note, self.velocity))
            time.sleep(duration)
            self.__class__.midiout.send_message(
                (NOTE_OFF + self.channel, note, 0))

        # Record time at which last composition completed.
        self.__class__.time_lastPlayed = self.__class__.timer()

    @staticmethod
    def serial_message_builder(note: int, duration: float):
        # Convert MIDI note number to an integer in [0, 11].
        note = map_0to127_to_0to11[note]
        # Convert seconds to microseconds, dropping any fractional part.
        duration = int(duration * 1_000_000)

        # Create an 11-element zero-filled bytearray.
        message = bytearray(11)

        # Message starts with character '%'.
        message[0] = ord("%")
        # Determines the "mode".
        message[1] = ord("2")
        # Determines the "note".
        message[2] = note
        # Determines the "duration".
        for idx, ch in enumerate(str(duration), start=3):
            message[idx] = ord(ch)
        # Message ends with character '&'.
        message[10] = ord("&")

        return message

    @classmethod
    def receive_response(cls):
        # Because a read timeout is set, this call will return immediately once
        # one byte (the requested number) is available; otherwise, wait until
        # the timeout expires. A timeout exception is not raised in the event
        # of a timeout.
        m = cls.ser.read(size=1)
        if not m:
            logger.critical("No response from microcontroller. Restarting.")
            restart_computer()

    @classmethod
    def time_elapsed(cls):
        """
        Returns the number of seconds (float) since the last composition was
        played.
        """
        return cls.timer() - cls.time_lastPlayed

    @classmethod
    def is_time(cls, seconds) -> bool:
        """
        Return `True` iff at least `seconds` seconds has elapsed since a
        composition has been played.
        """
        return cls.time_elapsed() >= seconds

    @classmethod
    def play_n(cls, n, drone=None):
        if drone is not None:
            drone.off()

        for i in range(n):
            comp = cls.from_random(bpm=cls.bpm)
            comp.play()


###############################################################################
#   Drone class: For TheNewArk, there is one drone on MIDI channel 2 (1-based
#                indexing) with MIDI note number 24 (0-based indexing).
###############################################################################
class Drone:
    """Drone object."""
    midiout = midiout
    ser = ser
    timer = perf_counter

    serial_on_message = b"%1" + b"\0" * 8 + b"&"
    serial_off_message = b"%0" + b"\0" * 8 + b"&"
    serial_n = 11

    assert len(serial_on_message) == len(serial_off_message) == serial_n

    def __init__(self, *, channel, note, velocity):
        """
        The zero-based indexing interpretation of the arguments are applied.
        """
        self.channel = channel
        self.note = note
        self.velocity = velocity

        self.on_message = (NOTE_ON + channel, note, velocity)
        self.off_message = (NOTE_OFF + channel, note, 0)

        # True iff drone is on.
        self.is_on = False

    def on(self):
        """Turns on the drone."""
        if not self.is_on:
            n = self.ser.write(self.serial_on_message)
            if n < self.serial_n:
                logger.critical("on(): Not all 'drone on' message bytes "
                                "written through USB-Serial. Restarting.")
                restart_computer()

            # Receive a response from microcontroller or restart otherwise.
            self.receive_response()

            self.midiout.send_message(self.on_message)
            self.is_on = True

            logger.info("Drone on.")

    def off(self):
        """Turns off the drone."""
        if self.is_on:
            n = self.ser.write(self.serial_off_message)
            if n < self.serial_n:
                logger.critical("off(): not all 'drone off' message bytes "
                                "written through USB-Serial. Restarting.")
                restart_computer()

            # Receive a response from microcontroller or restart otherwise.
            self.receive_response()

            self.midiout.send_message(self.off_message)
            self.is_on = False

            logger.info("Drone off.")

    def __del__(self):
        """Turns off the drone."""
        logger.info("Drone destructor. Turning drone off.")
        self.off()

    @classmethod
    def receive_response(cls):
        # Because a read timeout is set, this call will return immediately once
        # one byte (the requested number) is available; otherwise, wait until
        # the timeout expires. A timeout exception is not raised in the event
        # of a timeout.
        m = cls.ser.read(size=1)
        if not m:
            logger.critical("No response from microcontroller. Restarting.")
            restart_computer()
