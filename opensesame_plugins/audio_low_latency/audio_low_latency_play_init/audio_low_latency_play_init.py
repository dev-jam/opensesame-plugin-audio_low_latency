"""
This file is part of OpenSesame.

OpenSesame is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

OpenSesame is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with OpenSesame.  If not, see <http://www.gnu.org/licenses/>.
"""

__author__ = "Bob Rosbag"
__license__ = "GPLv3"

from ..audio_low_latency_init_item import AudioLowLatencyInitItem
from ..qt_audio_low_latency_init_item import QtAudioLowLatencyInitItem


class AudioLowLatencyPlayInit(AudioLowLatencyInitItem):

    kind = 'play'


class QtAudioLowLatencyPlayInit(AudioLowLatencyPlayInit, QtAudioLowLatencyInitItem):

    def __init__(self, name, experiment, script=None):
        AudioLowLatencyPlayInit.__init__(self, name, experiment, script)
        QtAudioLowLatencyInitItem.__init__(self, __file__)
