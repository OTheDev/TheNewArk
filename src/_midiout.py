###############################################################################
#   Imports
###############################################################################
import rtmidi
import sys

from _midi_constants import NOTE_OFF, N_CHANNELS, N_PITCHES


###############################################################################
#   Logging
###############################################################################
import logging
logger = logging.getLogger()


###############################################################################
#   MidiOut class
###############################################################################
class MidiOut(rtmidi.MidiOut):
    def __init__(self):
        """Initializer"""
        try:
            rtmidi.MidiOut.__init__(self)
        except rtmidi.SystemError:
            # Raised whenever the `rtmidi` backend initialization fails.
            logger.critical("rtmidi backend initialization failed!",
                            exc_info=True)
            sys.exit()
        # Returns a list of names of available MIDI input/output ports.
        # The zero-based index corresponding to a name in this list is
        # the port's "number".
        available_ports = self.get_ports()

        if available_ports:
            if len(available_ports) == 1:
                # Open the MIDI input/output port with port number `0`.
                # Only one port can be opened per MidiIn/MidiOut instance.
                # `open_port` cannot fail the way it is being used.
                self.open_port(0)
            elif len(available_ports) == 2:
                self.open_port(1)
            else:
                _e = ("There exists an available MIDI port but the program "
                      "is unable to find the correct one.")
                logger.critical(_e)
                sys.exit()
        else:
            logger.critical("No available MIDI ports!")
            sys.exit()

        self._notes_off()

    def _notes_off(self):
        """Turns off all notes on all MIDI channels."""
        for i in range(N_CHANNELS):     # for each possible channel    [0, 15]
            for j in range(N_PITCHES):  # for each possible note pitch [0, 127]
                self.send_message((NOTE_OFF + i, j, 0))

    def _notes_off_c0(self):
        """Turns off all notes on MIDI channel 0."""
        for j in range(N_PITCHES):
            self.send_message((NOTE_OFF, j, 0))

    def _notes_off_c(self, channel):
        """Turns off all notes on MIDI channel `channel`."""
        for j in range(N_PITCHES):
            self.send_message((NOTE_OFF + channel, j, 0))

    def __del__(self):
        """Finalizer. During program execution, if a 'note on' message is sent
        but a corresponding 'note off' message is not sent, then if the program
        terminates, for whatever reason, that note may continue to play
        forever. Hence, we call `_notes_off` in the destructor. This may not
        be called if run through an IDE such as Sublime Text 4. It is advised
        that the program is run from the terminal."""
        try:
            rtmidi.MidiOut.__del__(self)
        except AttributeError:
            # The base class does not have a __del__() method.
            pass
        self._notes_off()
