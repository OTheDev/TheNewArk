###############################################################################
#   Imports
###############################################################################
import glob
import platform
import serial
import sys


###############################################################################
#   Logging
###############################################################################
import logging
logger = logging.getLogger()


###############################################################################
#   Serial class: Finds an available serial port. For our purposes, we have
#                 a USB-A <-> Micro-USB cable where the USB-A connects to
#                 the computer and the Micro-USB connects to the Teensy
#                 4.0 on the micro-controller board controlling the lights.
#
#                 On my macOS and Linux systems, `devices` is a 1-element
#                 list. This is detectable when the Teensy 4.0 and computer
#                 are connected via the USB-A <-> Micro-USB cable.
#
#                 TheNewArk project uses two methods inherited from
#                 `serial.Serial`: `read(size=1)` and `write(data)`.
#                 The methods `read(size=1)` and `write(data)` may raise
#                 `serial.SerialException` when applied to a closed port.
#                 One possibility is that the program is running but
#                 some external factor causes the USB-A <-> Micro-USB
#                 cable to disconnect. There is not a direct way for the
#                 Teensy 4.0 program to know that the USB-Serial connection
#                 has been disconnected. A decision was made to terminate
#                 the entire program if the cable is disconnected. The
#                 program architecture assumes all hardware components are
#                 connected.
#
#                 The method `write(data)` may additionally raise
#                 `serial.SerialTimeoutException` if a write timeout is
#                 configured for the port and it is exceeded. There is not a
#                 write timeout configured. `read(size=1)` does not
#                 additionally raise `serial.SerialTimeoutException` in the
#                 event of a timeout.
###############################################################################
class Serial(serial.Serial):
    def __init__(self, port=None, baudrate=9600, timeout=None,
                 write_timeout=None):
        # Find port
        if port is None:
            system = platform.system()
            if system == "Darwin":
                # macOS
                devices = glob.glob("/dev/cu.usbmodem*")
            elif system == "Linux":
                # Linux
                devices = glob.glob("/dev/ttyACM*")
            else:
                logger.critical("This program is not supported on your "
                                "system. Supported systems: macOS, Linux.")
                sys.exit()

            if len(devices) == 1:
                port = devices[0]
            else:
                logger.critical("Found zero or more than one USB-Serial with "
                                "CDC-ACM profile. Please ensure that there is "
                                "a USB-A <-> Micro-USB connection between the "
                                "master computer and the micro-controller "
                                "prior to startup.")
                sys.exit()

        # Call the base class's __init__() method.
        try:
            super().__init__(port=port, baudrate=baudrate, timeout=timeout,
                             write_timeout=write_timeout)
        except serial.SerialException:
            message = (f"serial.SerialException: Device '{port}' cannot be "
                       "found or cannot be configured. Please ensure that "
                       "there is a USB-A <-> Micro-USB connection between the "
                       "master computer and the micro-controller prior to "
                       "startup.")
            logger.critical(message, exc_info=True)
            sys.exit()
        except ValueError:
            logger.critical("At least one of the parameters to `Serial()` are "
                            "out of range!", exc_info=True)
            sys.exit()
