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


class AudioLowLatencyPlayWait(Item):

    def prepare(self):
        super().prepare()
        self._check_init()
        self._init_var()

    def run(self):
        self._check_play()
        self.set_item_onset()

        if self.dummy_mode == 'no':
            while not self.experiment.audio_low_latency_play_thread_running:
                self.clock.sleep(POLL_TIME)
            if self.experiment.audio_low_latency_play_locked:
                self.experiment.audio_low_latency_play_thread.join()
            self.experiment.audio_low_latency_play_thread_running = 0
        elif self.dummy_mode == 'yes':
            self._show_message('Dummy mode enabled, NOT playing audio')
        else:
            self._show_message('Error with dummy mode!')

    def _init_var(self):
        self.dummy_mode = self.experiment.audio_low_latency_play_dummy_mode
        self.verbose = self.experiment.audio_low_latency_play_verbose
        self.experiment.audio_low_latency_play_wait = True

    def _check_play(self):
        if not self.experiment.audio_low_latency_play_start:
            raise OSException(
                    '`Audio Low Latency Play Start` item is missing')

    def _check_init(self):
        if not hasattr(self.experiment, 'audio_low_latency_play_device'):
            raise OSException(
                '`Audio Low Latency Play Init` item is missing')

    def _show_message(self, message):
        oslogger.debug(message)
        if self.verbose == 'yes':
            print(message)


class QtAudioLowLatencyPlayWait(AudioLowLatencyPlayWait, QtAutoPlugin):

    def __init__(self, name, experiment, script=None):
        AudioLowLatencyPlayWait.__init__(self, name, experiment, script)
        QtAutoPlugin.__init__(self, __file__)
