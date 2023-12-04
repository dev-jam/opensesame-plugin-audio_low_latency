#-*- coding:utf-8 -*-

"""
Author: Bob Rosbag
2022

This plug-in is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This software is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this plug-in.  If not, see <http://www.gnu.org/licenses/>.
"""

from libopensesame.py3compat import *
from libopensesame.item import Item
from libqtopensesame.items.qtautoplugin import QtAutoPlugin
from libopensesame.exceptions import OSException
from libopensesame.oslogging import oslogger

POLL_TIME = 100


class AudioLowLatencyPlayResume(Item):

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
            self._show_message('Sending resume signal')
            self.experiment.audio_low_latency_play_execute_pause = 0
        elif self.dummy_mode == 'yes':
            self._show_message('Dummy mode enabled, NOT playing audio')
        else:
            self._show_message('Error with dummy mode!')

    def _init_var(self):
        self.dummy_mode = self.experiment.audio_low_latency_play_dummy_mode
        self.verbose = self.experiment.audio_low_latency_play_verbose
        self.experiment.audio_low_latency_play_resume = True

    def _check_init(self):
        if not hasattr(self.experiment, 'audio_low_latency_play_device'):
            raise OSException(
                '`Audio Low Latency Play Init` item is missing')

    def _check_play(self):
        if not self.experiment.audio_low_latency_play_start:
            raise OSException(
                    '`Audio Low Latency Play Start` item is missing')

    def _check_pause_resume(self):
        if not self.experiment.audio_low_latency_play_pause_resume_key and not self.experiment.audio_low_latency_play_pause:
            raise OSException('`Audio Low Latency Play Resume` item is missing a resume/pause key or item')

    def _show_message(self, message):
        oslogger.debug(message)
        if self.verbose == 'yes':
            print(message)


class QtAudioLowLatencyPlayResume(AudioLowLatencyPlayResume, QtAutoPlugin):

    def __init__(self, name, experiment, script=None):
        AudioLowLatencyPlayResume.__init__(self, name, experiment, script)
        QtAutoPlugin.__init__(self, __file__)
