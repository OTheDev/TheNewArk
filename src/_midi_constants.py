# Status bytes for Channel Voice Messages. n an arbitrary hex digit.
NOTE_OFF          = 0x80  # 0x8n # noqa: E221
NOTE_ON           = 0x90  # 0x9n # noqa: E221
CONTROL_CHANGE    = 0xB0  # 0xBn # noqa: E221
PROGRAM_CHANGE    = 0xC0  # 0xCn # noqa: E221
PITCH_BEND        = 0xE0  # 0xEn # noqa: E221
CHANNEL_PRESSURE  = 0xD0  # 0xDn # noqa: E221
POLY_KEY_PRESSURE = 0xA0  # 0xAn # noqa: E221

# Bank Selection. Either one of these follow a Control Change Status byte.
BANK_SELECT_MSB = 0x00
BANK_SELECT_LSB = 0x20

# Channel Mode Messages. Same Status Byte as a Control Change message.
# There is no requirement that a receiver recognize an ALL NOTES OFF mode
# message. "Thus, all notes should first be turned off by transmitting
# individual Note Off messages prior to sending an All Notes Off"
# (MIDI 1.0 Specification).
ALL_SOUND_OFF         = 120  # 0x78 # noqa: E221
RESET_ALL_CONTROLLERS = 121  # 0x79 # noqa: E221
LOCAL_CONTROL         = 122  # 0x7A # noqa: E221
ALL_NOTES_OFF         = 123  # 0x7B # noqa: E221
OMNI_OFF              = 124  # 0x7C # noqa: E221
OMNI_ON               = 125  # 0x7D # noqa: E221
MONO_ON_POLY_OFF      = 126  # 0x7E # noqa: E221
POLY_ON_MONO_OFF      = 127  # 0x7F # noqa: E221

# Other useful constants.
N_CHANNELS = 16
N_PITCHES = 128
N_PKEYS = 88
MIDI_NOTE_NAMES = (
    # lower end
    "C-1", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B",
    "C0", "C#", "D", "D#", "E", "F", "F#", "G", "G#",
    # piano keys
    "A0", "A#0/Bb0", "B0",
    "C1", "C#1/Db1", "D1", "D#1/Eb1", "E1", "F1", "F#1/Gb1", "G1", "G#1/Ab1", "A1", "A#1/Bb1", "B1", # noqa: E501
    "C2", "C#2/Db2", "D2", "D#2/Eb2", "E2", "F2", "F#2/Gb2", "G2", "G#2/Ab2", "A2", "A#2/Bb2", "B2", # noqa: E501
    "C3", "C#3/Db3", "D3", "D#3/Eb3", "E3", "F3", "F#3/Gb3", "G3", "G#3/Ab3", "A3", "A#3/Bb3", "B3", # noqa: E501
    "C4", "C#4/Db4", "D4", "D#4/Eb4", "E4", "F4", "F#4/Gb4", "G4", "G#4/Ab4", "A4", "A#4/Bb4", "B4", # noqa: E501
    "C5", "C#5/Db5", "D5", "D#5/Eb5", "E5", "F5", "F#5/Gb5", "G5", "G#5/Ab5", "A5", "A#5/Bb5", "B5", # noqa: E501
    "C6", "C#6/Db6", "D6", "D#6/Eb6", "E6", "F6", "F#6/Gb6", "G6", "G#6/Ab6", "A6", "A#6/Bb6", "B6", # noqa: E501
    "C7", "C#7/Db7", "D7", "D#7/Eb7", "E7", "F7", "F#7/Gb7", "G7", "G#7/Ab7", "A7", "A#7/Bb7", "B7", # noqa: E501
    # last piano key
    "C8",
    # upper end
    "C#8/Db8", "D8", "D#8/Eb8", "E8", "F8", "F#8/Gb8", "G8", "G#8/Ab8", "A8",
    "A#8/Bb8", "B8", "C9", "C#9/Db9", "D9", "D#9/Eb9", "E9", "F9", "F#9/Gb9",
    "G9"
    )
MIN_VELOCITY = 0
MAX_VELOCITY = 127
