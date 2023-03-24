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

#import warnings

from libopensesame.py3compat import *
from libopensesame import debug
from libopensesame.item import item
from libqtopensesame.items.qtautoplugin import qtautoplugin
from libopensesame.exceptions import osexception
from openexp.keyboard import keyboard

VERSION = u'9.1.0'

class audio_low_latency_record_wait(item):

    description = u'Low Latency Audio: waits until the background audio recording has finished.'

    def __init__(self, name, experiment, string=None):

        item.__init__(self, name, experiment, string)
        self.verbose = u'no'
        self.poll_time = 100

    def reset(self):

        pass

    def init_var(self):

        if hasattr(self.experiment, "audio_low_latency_record_dummy_mode"):
            self.dummy_mode = self.experiment.audio_low_latency_record_dummy_mode
            self.verbose = self.experiment.audio_low_latency_record_verbose
        else:
            raise osexception(
                    u'Audio Low Latency Record Init item is missing')

        self.experiment.audio_low_latency_record_wait = 1

    def prepare(self):

        item.prepare(self)

        self.init_var()

        # create keyboard object
        self.kb = keyboard(self.experiment,timeout=1)

    def run(self):

        if not hasattr(self.experiment, "audio_low_latency_record_start"):
            raise osexception(
                    u'Audio Low Latency Record Start item is missing')

        self.set_item_onset()

        if self.dummy_mode == u'no':

            ## wait if thread has not started yet
            while not self.experiment.audio_low_latency_record_thread_running:
                self.clock.sleep(self.poll_time)

            ## join thread if thread is still running
            if self.experiment.audio_low_latency_record_locked:
                self.experiment.audio_low_latency_record_thread.join()

            ## set end of thread
            self.experiment.audio_low_latency_record_thread_running = 0


        elif self.dummy_mode == u'yes':
            self.show_message(u'Dummy mode enabled, NOT recording audio')
        else:
            self.show_message(u'Error with dummy mode!')

    def show_message(self, message):

        debug.msg(message)
        if self.verbose == u'yes':
            print(message)


class qtaudio_low_latency_record_wait(audio_low_latency_record_wait, qtautoplugin):

    def __init__(self, name, experiment, script=None):

        audio_low_latency_record_wait.__init__(self, name, experiment, script)
        qtautoplugin.__init__(self, __file__)
