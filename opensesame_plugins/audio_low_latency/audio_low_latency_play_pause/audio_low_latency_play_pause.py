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

from libopensesame.py3compat import *
from libopensesame.item import Item
from libqtopensesame.items.qtautoplugin import QtAutoPlugin
from libopensesame.exceptions import OSException
from libopensesame.oslogging import oslogger

POLL_TIME = 100


class AudioLowLatencyPlayPause(Item):

    def prepare(self):
        super().prepare()
        self._check_init()
        self._init_var()

    def run(self):
        self._check_play()
        self._check_pause_resume()
        self.set_item_onset()

        if self.dummy_mode == 'no':
            while not self.experiment.audio_low_latency_play_thread_running:
                self.clock.sleep(POLL_TIME)
            self._show_message('Sending pause signal')
            self.experiment.audio_low_latency_play_execute_pause = 1
        elif self.dummy_mode == 'yes':
            self._show_message('Dummy mode enabled, NOT playing audio')
        else:
            self._show_message('Error with dummy mode!')

    def _init_var(self):
        self.dummy_mode = self.experiment.audio_low_latency_play_dummy_mode
        self.verbose = self.experiment.audio_low_latency_play_verbose
        self.experiment.audio_low_latency_play_pause = True

    def _check_init(self):
        if not hasattr(self.experiment, 'audio_low_latency_play_device'):
            raise OSException(
                '`Audio Low Latency Play Init` item is missing')

    def _check_play(self):
        if not self.experiment.audio_low_latency_play_start:
            raise OSException(
                    '`Audio Low Latency Play Start` item is missing')

    def _check_pause_resume(self):
        if not self.experiment.audio_low_latency_play_pause_resume_key and not self.experiment.audio_low_latency_play_resume:
            raise OSException('`Audio Low Latency Play Pause` item is missing a resume/pause key or item')

    def _show_message(self, message):
        oslogger.debug(message)
        if self.verbose == 'yes':
            print(message)


class QtAudioLowLatencyPlayPause(AudioLowLatencyPlayPause, QtAutoPlugin):

    def __init__(self, name, experiment, script=None):
        AudioLowLatencyPlayPause.__init__(self, name, experiment, script)
        QtAutoPlugin.__init__(self, __file__)
