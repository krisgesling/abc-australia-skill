# Copyright 2022 Mycroft AI Inc.
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
"""Defines a News Station object"""

from builtins import property
from dataclasses import dataclass
from pathlib import Path

from mycroft.util import LOG


@dataclass(frozen=True)
class Station:
    """ABC News Station."""

    name: str
    aliases: list
    # Images for each station can be found at: https://www.abc.net.au/radio/stations/
    image_file: str
    color: str
    # Stream urls in the form {base_url}/{format}/station.pls
    # eg http://www.abc.net.au/res/streaming/audio/mp3/news_radio.pls
    # Streams defined at: https://help.abc.net.au/hc/en-us/articles/4402927208079-Where-can-I-find-direct-stream-URLs-for-ABC-Radio-stations-
    stream: str
    base_url: str = "http://www.abc.net.au/res/streaming/audio/"

    @property
    def as_dict(self):
        return {
            "name": self.name,
            "image_path": str(self.image_path),
        }

    @property
    def image_path(self) -> Path:
        """The absolute path to the stations logo.

        Note that this currently traverses the path from this file and may
        break if this is moved in the file hierarchy.
        """
        if self.image_file is None:
            return None
        skill_path = Path(__file__).parent.parent.absolute()
        file_path = Path(skill_path, "ui", "station-logos", self.image_file)
        if not file_path.exists():
            LOG.warning(f"{self.image_file} could not be found, using default image")
            file_path = Path(skill_path, "images", "generic.png")
        return file_path

    @property
    def mp3_stream(self) -> str:
        """The MP3 stream url."""
        return f"{self.base_url}/mp3/{self.stream}"

    @property
    def aac_stream(self) -> str:
        """The AAC+ stream url."""
        return f"{self.base_url}/aac/{self.stream}"


stations = [
    Station(
        name="ABC News",
        aliases=[],
        image_file="abc-news.png",
        color="#000000",
        stream="news_radio.pls",
    ),
    Station(
        name="ABC Radio National",
        aliases=["ABC RN"],
        image_file="abc-radio-national.png",
        color="#ac1c1c",
        stream="radio_national.pls",
    ),
    Station(
        name="ABC Sport",
        aliases=[],
        image_file="abc-sport.png",
        color="#2eab2b",
        stream="grandstand.pls",
    ),
    Station(
        name="triple j",
        aliases=[],
        image_file="triple-j.png",
        color="#E03125",
        stream="triplej.pls",
    ),
    Station(
        name="triple j Unearthed",
        aliases=["unearthed"],
        image_file="unearthed.png",
        color="#3f752c",
        stream="unearthed.pls",
    ),
    Station(
        name="Double J",
        aliases=["dig music"],
        image_file="double-j.png",
        color="#000000",
        stream="dig_music.pls",
    ),
    # Station(
    #     name="",
    #     aliases=[],
    #     image_file=".png",
    #     color="#",
    #     stream=""
    # ),
]
