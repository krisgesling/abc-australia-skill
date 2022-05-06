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

import enum
from collections import namedtuple

from mycroft.util import LOG
from mycroft.util.parse import fuzzy_match

from .station import stations


class MatchConfidence(enum.Enum):
    """Minimum confidence levels for Common Play matching"""

    EXACT = 0.9
    HIGH = 0.8
    LIKELY = 0.7
    GENERIC = 0.6


Match = namedtuple("Match", "station confidence")


def match_station_name(phrase, station):
    """Determine confidence that a phrase requested a given station.

    Args:
        phrase (str): utterance from the user
        station (str): the station feed to match against

    Returns:
        tuple: feed being matched, highest confidence level found
    """
    phrase = phrase.lower().replace("play", "").strip()

    match_confidences = [
        fuzzy_match(phrase, station.name.lower()),
    ]
    match_confidences.extend(
        [fuzzy_match(phrase, alias.lower()) for alias in station.aliases]
    )

    highest_confidence = max(match_confidences)
    return Match(station, highest_confidence)


def match_station_from_utterance(skill, utterance):
    """Get the expected station from a user utterance.

    Returns:
        Station or None if news not requested.
    """
    match = Match(None, 0.0)

    utterance = utterance.lower().strip()

    # Test against each station to find the best match.
    for station in stations:
        station_match = match_station_name(utterance, station)
        if station_match.confidence > match.confidence:
            match = station_match

    return match
