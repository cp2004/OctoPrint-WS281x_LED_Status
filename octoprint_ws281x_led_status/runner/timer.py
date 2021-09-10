# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, unicode_literals

__author__ = "Charlie Powell <cp2004.github@gmail.com"
__license__ = "GNU Affero General Public License https://www.gnu.org/licenses/agpl.html"
__copyright__ = (
    "Copyright (c) Charlie Powell 2021 - released under the terms of the AGPLv3 License"
)

from datetime import datetime

from octoprint.util import RepeatedTimer

# TODO Test this whole module in Python 2...


class ActiveTimer:
    def __init__(self, settings, callback):
        self.switch_callback = callback  # Callable with arguments: state (bool)
        self.settings = settings  # dict of settings from OctoPrint, see settings.py

        self.active = True

        self.start_time = list(
            map(lambda x: int(x), self.settings["start"].split(":"))
        )  # [hh, mm]
        self.end_time = list(
            map(lambda x: int(x), self.settings["end"].split(":"))
        )  # [hh, mm]

        if settings["enabled"]:
            # Only create the timer if necessary, as minimal logic as possible
            self.timer = self.timer = RepeatedTimer(
                30,  # TODO reduce to 30
                self.check_times,
                run_first=True,
            )
        else:
            self.timer = None

    def switch(self, state):
        self.active = state
        self.switch_callback(state)

    def start_timer(self):
        if self.timer:
            self.timer.start()

    def end_timer(self):
        if self.timer:
            self.timer.cancel()  # Breaks loop & exits timer

    def check_times(self):
        # When should lights turn on *today*
        start = datetime.now().replace(
            hour=self.start_time[0], minute=self.start_time[1]
        )
        # When should lights turn off *today*
        end = datetime.now().replace(hour=self.end_time[0], minute=self.end_time[1])

        if not (end - start).total_seconds() > 0:
            # If start is not before end, this is not supported & lights will always be on
            # Don't even bother trying to calculate it..
            self.switch(True)
            return

        current = datetime.now()

        if (current - start).total_seconds() > 0:
            # After start time, so lights should probably be on
            if (end - current).total_seconds() > 0:
                # Before end time, lights should definitely be on
                self.switch(True)
                return

        self.switch(False)
