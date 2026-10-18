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


class AudioLowLatencyRecordWait(Item):

    def prepare(self):
        super().prepare()
        self._check_init()
        self._init_var()

    def run(self):
        self._check_record()
        self.set_item_onset()

        if self.dummy_mode == 'no':
            self._check_thread_running()
            self.experiment.audio_low_latency_record_thread.join()
            self.experiment.audio_low_latency_record_thread_running = 0
            self._check_thread_error()
        elif self.dummy_mode == 'yes':
            self._show_message('Dummy mode enabled, NOT recording audio')
        else:
            self._show_message('Error with dummy mode!')

    def _init_var(self):
        self.dummy_mode = self.experiment.audio_low_latency_record_dummy_mode
        self.verbose = self.experiment.audio_low_latency_record_verbose
        self.experiment.audio_low_latency_record_wait = 1

    def _check_record(self):
        if not getattr(self.experiment, 'audio_low_latency_record_start', False):
            raise OSException(
                'Audio Low Latency Record Start item is missing')

    def _check_init(self):
        if not hasattr(self.experiment, 'audio_low_latency_record_device'):
            raise OSException(
                'Audio Low Latency Record Init item is missing')

    def _check_thread_running(self):
        if not self.experiment.audio_low_latency_record_thread_running:
            raise OSException(
                '`Audio Low Latency Record Start` did not run before this item')

    def _check_thread_error(self):
        error = self.experiment.audio_low_latency_record_thread_error
        if error is not None:
            self.experiment.audio_low_latency_record_thread_error = None
            if isinstance(error, OSException):
                raise error
            raise OSException(
                f'Background audio recording failed\n\nMessage: {error}') from error

    def _show_message(self, message):
        oslogger.debug(message)
        if self.verbose == 'yes':
            print(message)


class QtAudioLowLatencyRecordWait(AudioLowLatencyRecordWait, QtAutoPlugin):

    def __init__(self, name, experiment, script=None):
        AudioLowLatencyRecordWait.__init__(self, name, experiment, script)
        QtAutoPlugin.__init__(self, __file__)

