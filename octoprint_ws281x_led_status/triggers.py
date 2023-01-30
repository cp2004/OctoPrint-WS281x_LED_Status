import logging
import re

from octoprint.events import all_events


class Trigger:
    def __init__(self, effect_queue):
        self._logger = logging.getLogger("octoprint.plugins.ws281x_led_status.triggers")

        self.at_command_subscriptions = []
        self.event_subscriptions = []
        self.gcode_command_subscriptions = []
        self.gcode_exact_subscriptions = []
        self.gcode_regex_subscriptions = []

        self.effect_queue = effect_queue

    def register_atcommand_handler(self, match, effect, color, delay):
        """
        command: @WS CUSTOM <command>
        effect: Name from constants.EFFECTS
        color: Hex colour
        delay: ms between frames
        """
        self.at_command_subscriptions.append(
            {
                "match": match,
                "effect": effect,
                "color": color,
                "delay": delay,
            }
        )

    def register_event_handler(self, match, effect, color, delay):
        """
        event: event from `octoprint.events.Events`
        effect: Name from constants.EFFECTS
        color: Hex colour
        delay: ms between frames
        """
        if match not in all_events():
            self._logger.warning(f"Event ({match}) not available, ignoring")
            return
        self.event_subscriptions.append(
            {
                "match": match,
                "effect": effect,
                "color": color,
                "delay": delay,
            }
        )

    def register_gcode_handler(self, match_type, match, effect, color, delay):
        """
        match_type: 'gcode', 'exact', 'regex'
        match: string to match command against
        effect: Name from constants.EFFECTS
        color: Hex colour
        delay: ms between frames
        """
        subscription = {
            "match": match,
            "effect": effect,
            "color": color,
            "delay": delay,
        }
        if match_type == "gcode":
            self.gcode_command_subscriptions.append(subscription)
        elif match_type == "exact":
            self.gcode_exact_subscriptions.append(subscription)
        elif match_type == "regex":
            self.gcode_regex_subscriptions.append(subscription)

    def reset_subscriptions(self):
        self.event_subscriptions = []
        self.gcode_command_subscriptions = []
        self.gcode_exact_subscriptions = []
        self.gcode_regex_subscriptions = []
        self.at_command_subscriptions = []

    def process_settings(self, settings):
        # Convert the settings into subscriptions
        self.reset_subscriptions()
        for entry in settings["atcommand"]:
            try:
                self.register_atcommand_handler(
                    entry["match"],
                    entry["effect"],
                    entry["color"],
                    entry["delay"],
                )
            except Exception as e:
                self._logger.warning(
                    "Failed to add atcommand entry to subscriptions, ignoring"
                )
                self._logger.exception(e)

        for entry in settings["event"]:
            try:
                self.register_event_handler(
                    entry["match"],
                    entry["effect"],
                    entry["color"],
                    entry["delay"],
                )
            except Exception as e:
                self._logger.warning(
                    "Failed to add event entry to subscriptions, ignoring"
                )
                self._logger.exception(e)

        for entry in settings["gcode"]:
            try:
                self.register_gcode_handler(
                    entry["match_type"],
                    entry["match"],
                    entry["effect"],
                    entry["color"],
                    entry["delay"],
                )
            except Exception as e:
                self._logger.warning(
                    "Failed to add gcode entry to subscriptions, ignoring"
                )
                self._logger.exception(e)

    def on_event(self, event):
        for event in self.event_subscriptions:
            if event["match"] == event:
                self.effect_queue.put(
                    {
                        "type": "custom",
                        "effect": event["effect"],
                        "color": event["color"],
                        "delay": event["delay"],
                        "trigger": "event: {}".format(event["match"]),
                    }
                )

    def on_at_command(self, command):
        """
        Command should be pre-stripped of @WS CUSTOM <command>, to just be command
        """
        for at_command in self.at_command_subscriptions:
            if at_command["match"].upper() == command:
                self.effect_queue.put(
                    {
                        "type": "custom",
                        "effect": at_command["effect"],
                        "color": at_command["color"],
                        "delay": at_command["delay"],
                        "trigger": "at command: {}".format(at_command["match"]),
                    }
                )

    def on_gcode_command(self, gcode, cmd):
        # TODO any performance optimisations?
        for gcode_command in self.gcode_command_subscriptions:
            # Match only G/M code
            if gcode_command["match"] == gcode:
                self.effect_queue.put(
                    {
                        "type": "custom",
                        "effect": gcode_command["effect"],
                        "color": gcode_command["color"],
                        "delay": gcode_command["delay"],
                        "trigger": "gcode match: {}".format(gcode_command["match"]),
                    }
                )
                # Once we have a match, we can stop looking
                break
        for gcode_exact in self.gcode_exact_subscriptions:
            # Match whole line sent to printer
            if gcode_exact["match"] == cmd:
                self.effect_queue.put(
                    {
                        "type": "custom",
                        "effect": gcode_exact["effect"],
                        "color": gcode_exact["color"],
                        "delay": gcode_exact["delay"],
                        "trigger": "gcode exact: {}".format(gcode_exact["match"]),
                    }
                )
                # Once we have a match, we can stop looking
                break

        for gcode_regex in self.gcode_regex_subscriptions:
            # Match cmd by regex
            if re.match(gcode_regex["match"], cmd):
                self.effect_queue.put(
                    {
                        "type": "custom",
                        "effect": gcode_regex["effect"],
                        "color": gcode_regex["color"],
                        "delay": gcode_regex["delay"],
                        "trigger": "gcode regex: {}".format(gcode_regex["match"]),
                    }
                )
                # Once we have a match, we can stop looking
                break
