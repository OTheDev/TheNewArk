###############################################################################
#   Logging
###############################################################################
import logging
import logging.config
import os

logging.config.fileConfig('_logging.conf')

# Create logger.
logger = logging.getLogger(__name__)


###############################################################################
#   Imports: violates PEP 8 (E402). Logging configuration appears before
#            imports so as to also log any warnings that occur during import.
###############################################################################
import datetime                                  # noqa: E402
import http.client                               # noqa: E402
import os                                        # noqa: E402
import pickle                                    # noqa: E402
import requests                                  # noqa: E402
import sys                                       # noqa: E402

from ast import literal_eval                     # noqa: E402
from functools import partial                    # noqa: E402
from math import floor                           # noqa: E402
from random import randint, sample, shuffle      # noqa: E402
from time import localtime, perf_counter, sleep  # noqa: E402

from _composition import Composition, Drone      # noqa: E402
from _macapps import MacApps                     # noqa: E402
from _scheduler import Scheduler                 # noqa: E402
from _tonerow import is_tonerow, _random         # noqa: E402


###############################################################################
#   Globals - Web Service
#
#   payload    : Payload for `UpdateToneRowByIds`. This is modified in-place
#                and reused. The "twelveToneMatrix" field will be the string
#                representation of a two-element list of lists where the first
#                list is a 48-element list of MIDI note numbers and the second
#                list is a 48-element list of durations in seconds.
#
#  payload_nce : Payload for `NotifyCompositionEnd`. This is modified in-place
#                and reused.
###############################################################################
root_url = os.environ["TNA_ROOTURL"]
urls = (
    root_url + "GetNewToneRows?type=user",
    root_url + "UpdateToneRowByIds",
    root_url + "NotifyCompositionEnd"
)
payload = [{
    "id": -1,
    "playedOn": "<time in ISO-8601 format as a string>",
    "twelveToneMatrix": "NA"
}]
payload_nce = {"id": -1}


###############################################################################
#   Globals - Other
#
#   comp_break       : at least `comp_break` seconds break in between
#                      compositions.
#
#   max_time_break   : maximum duration in seconds since a composition has
#                      been played to play drone sounds.
#
#   bpm              : beats-per-minute.
#
#   n_max_time_break : number of compositions to play after `max_time_break`
#                      seconds without a composition playing.
###############################################################################
comp_break = 1
max_time_break = 60 * 5
bpm = 102
n_max_time_break = 1
timeout = (10, 15)


###############################################################################
#   Helpers
###############################################################################
def get(*, url, timeout, drone, session, scheduler):
    first = True
    while True:
        try:
            r = session.get(url, timeout=timeout)

            if not first:
                logger.critical("TheNewArk should now be operating normally.")

            return r.json()
        except requests.exceptions.RequestException as err:
            if first:
                logger.critical("Please ensure there is internet.",
                                exc_info=True)
                first = False
                prev_e = err
            else:
                if not isinstance(err, type(prev_e)):
                    logger.critical(err, exc_info=True)
                    prev_e = err
            drone.on()
        except requests.exceptions.JSONDecodeError as err:
            # Raised if the response body does not contain valid json.
            logger.critical(err, exc_info=True)

            return []

        scheduler.check()


def post(*, url, json=None, params=None, timeout=None, drone, session,
         scheduler):
    first = True
    while True:
        try:
            session.post(url, json=json, params=params, timeout=timeout)
            break
        except requests.exceptions.RequestException as err:
            if first:
                logger.critical("Please ensure there is internet.",
                                exc_info=True)
                first = False
                prev_e = err
            else:
                if not isinstance(err, type(prev_e)):
                    logger.critical(err, exc_info=True)
                    prev_e = err
            drone.on()

        scheduler.check()

    if not first:
        logger.critical("TheNewArk should now be operating normally!")


def restart_OBS(apps):
    apps.close()
    sleep(3)
    apps.open()


###############################################################################
#   Main Function
###############################################################################
def main():
    # If there is no internet, can still get past this next line.
    session = requests.Session()

    # This Drone instance will be used for the entire session.
    drone = Drone(channel=1, note=24, velocity=60)

    # Open OBS.
    apps = MacApps(["OBS"])
    apps.open()

    # Scheduled events.
    is_time = partial(Composition.is_time, max_time_break)
    scheduler = Scheduler(every=[2 * 60 * 60, is_time],
                          callbacks=[restart_OBS, Composition.play_n],
                          args=[[apps], [n_max_time_break, drone]])
    while True:
        # GetNewToneRows.
        data = get(url=urls[0], timeout=timeout, drone=drone, session=session,
                   scheduler=scheduler)

        if data:
            # Turn off drone.
            drone.off()
            for e in data:
                try:
                    row = literal_eval(e["noteRow"])
                except (ValueError, TypeError, SyntaxError, MemoryError,
                        RecursionError):
                    # If for whatever reason input from the Web Service is
                    # malformed, create a random tonerow and use that.
                    logger.critical("Invalid input. Creating random tr.",
                                    exc_info=True)
                    row = _random()

                if not is_tonerow(row):
                    logger.critical("Invalid tr. Creating random tr.")
                    row = _random()

                # Create an instance of Composition.
                comp = Composition(row, bpm=bpm, ID=e["id"])

                # Before playing, let the web service know the composition ID,
                # the time in ISO-8601 format, and the generated composition
                # (defined by the 48 notes and 48 note durations).
                payload[0]["id"] = e["id"]
                payload[0]["playedOn"] = datetime.datetime.now().isoformat()
                payload[0]["twelveToneMatrix"] = ("[" + repr(comp.notes) + ", "
                                                  + repr(comp.durations) + "]")
                payload_nce["id"] = e["id"]

                # UpdateToneRowByIds.
                post(url=urls[1], json=payload, timeout=timeout, drone=drone,
                     session=session, scheduler=scheduler)

                # Turn off drone.
                drone.off()

                # Play composition.
                comp.play()

                # NotifyCompositionEnd.
                post(url=urls[2], params=payload_nce, timeout=timeout,
                     drone=drone, session=session, scheduler=scheduler)
        else:
            scheduler.check()

            # Turn on drone.
            drone.on()


###############################################################################
#   Main
###############################################################################
if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
