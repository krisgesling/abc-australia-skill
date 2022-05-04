# Copyright 2018 Mycroft AI Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import enum
from typing import Tuple

from mycroft import intent_handler, AdaptIntent
from mycroft.audio import wait_while_speaking
from mycroft.messagebus import Message
from mycroft.skills.common_play_skill import CommonPlaySkill, CPSMatchLevel

from .stations.match import match_station_from_utterance, Match, MatchConfidence
from .stations.station import Station, stations
from .stations.util import find_mime_type


class Status(enum.Enum):
    """Possible states of this Skill"""

    STOPPED = 1  # Media not playing or displayed
    PLAYING = 2  # Media is playing, display state unknowm
    PAUSED = 3  # Media paused, ready to resume


class ABCRadioSkill(CommonPlaySkill):
    def __init__(self) -> None:
        super().__init__()
        self.status = Status.STOPPED
        self.now_playing = None

    def initialize(self):
        self.platform = self.config_core["enclosure"].get("platform", "unknown")
        self.register_gui_handlers()
        self.disable_intent('handle_show_player')

    def register_gui_handlers(self):
        """Register handlers for events to or from the GUI."""
        self.bus.on(
            "mycroft.audio.service.pause", self.handle_audioservice_status_change
        )
        self.bus.on(
            "mycroft.audio.service.resume", self.handle_audioservice_status_change
        )
        self.bus.on("mycroft.audio.queue_end", self.handle_media_finished)
        self.gui.register_handler("cps.gui.pause", self.handle_gui_status_change)
        self.gui.register_handler("cps.gui.play", self.handle_gui_status_change)

    def handle_audioservice_status_change(self, message):
        """Handle changes in playback status from the Audioservice.

        Eg when someone verbally asks to pause.
        """
        if self.status == Status.STOPPED:
            return
        command = message.msg_type.split(".")[-1]
        if command == "resume":
            new_status = "Playing"
        elif command == "pause":
            new_status = "Paused"
        self.gui["status"] = new_status

    def handle_gui_status_change(self, message):
        """Handle play and pause status changes from the GUI.

        This notifies the audioservice. The GUI state only changes once the
        audioservice emits the relevant messages to say the state has changed.
        """
        if self.status == Status.STOPPED:
            return
        command = message.msg_type.split(".")[-1]
        if command == "play":
            self.log.info("Audio resumed by GUI.")
            self.bus.emit(Message("mycroft.audio.service.resume"))
        elif command == "pause":
            self.log.info("Audio paused by GUI.")
            self.bus.emit(Message("mycroft.audio.service.pause"))

    def handle_media_finished(self, _):
        """Handle media playback finishing."""
        if self.status == Status.PLAYING:
            self.gui.release()
            self.status = Status.STOPPED

    @intent_handler(AdaptIntent("").require("Show").require("Radio"))
    def handle_show_player(self, _):
        if self.status == Status.STOPPED:
            self.speak_dialog("no-station-playing")
        else:
            self._show_gui_page("AudioPlayer")

    def CPS_start(self, _, data):
        """Handle request from Common Play System to start playback."""
        self.log.error(data)
        for station in stations:
            self.log.info(station.name)
            if station.name == data["name"]:
                return self._play_station(station)
        self.log.error("FAIL")
        return

    def CPS_match_query_phrase(self, phrase: str) -> Tuple[str, float, dict]:
        """Respond to Common Play Service query requests.

        Args:
            phrase: utterance request to parse

        Returns:
            Tuple(Name of station, confidence, Station information)
        """
        match = match_station_from_utterance(self, phrase)

        # If no match but utterance contains news, return low confidence level
        if match.confidence < MatchConfidence.GENERIC.value:
            match = Match(self.get_default_station(), MatchConfidence.GENERIC)

        # Translate match confidence levels to CPSMatchLevels
        if match.confidence >= MatchConfidence.EXACT.value:
            match_level = CPSMatchLevel.EXACT
        elif match.confidence >= MatchConfidence.LIKELY.value:
            match_level = CPSMatchLevel.ARTIST
        elif match.confidence >= MatchConfidence.GENERIC.value:
            match_level = CPSMatchLevel.CATEGORY
        else:
            return None

        return match.station.name, match_level, match.station.as_dict

    def _play_station(self, station: Station):
        """Play the given station using the most appropriate service.

        Args:
            station (Station): Instance of a Station to be played
        """
        try:
            self.log.info(f"Playing station: {station.name}")
            self.enable_intent('handle_show_player')
            media_url = station.mp3_stream
            self.log.info(f"Station url: {media_url}")
            mime = find_mime_type(media_url)
            # Ensure announcement of station has finished before playing
            wait_while_speaking()

            # We support streaming
            self.CPS_play((media_url, mime))

            self.gui["media"] = {
                "image": str(station.image_path),
                "artist": station.name,
                "track": "",
                "album": "",
                "skill": self.skill_id,
                "streaming": True,
            }
            self.gui["status"] = "Playing"
            self.gui["theme"] = dict(fgColor="white", bgColor=station.color)
            self._show_gui_page("AudioPlayer")
            self.CPS_send_status(
                # cast to str for json serialization
                image=str(station.image_path),
                artist=station.name,
            )
            self.now_playing = station.name
        except ValueError as e:
            self.speak_dialog(
                "could-not-start-that-station", {"station_name": station.name}
            )
            self.log.exception(e)

    def _show_gui_page(self, page):
        """Show a page variation depending on platform."""
        if self.gui.connected:
            if self.platform == "mycroft_mark_2":
                qml_page = f"{page}_mark_ii.qml"
            else:
                qml_page = f"{page}_scalable.qml"
            self.gui.show_page(qml_page, override_idle=True)

    def stop(self) -> bool:
        """Respond to system stop commands."""
        if self.status == Status.STOPPED:
            return False
        self.now_playing = None
        self.disable_intent('handle_show_player')
        self.CPS_send_status()
        self.gui.release()
        self.CPS_release_output_focus()
        return True


def create_skill():
    return ABCRadioSkill()
