#-*- coding:utf-8 -*-

"""
Author: Bob Rosbag
2020

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

VERSION = u'8.6.0'

class audio_low_latency_play_resume(item):

    """
    Class handles the basic functionality of the item.
    It does not deal with GUI stuff.
    """

    # Provide an informative description for your plug-in.
    description = u'Low Latency Audio: stops the background audio playback.'

    def __init__(self, name, experiment, string=None):

        item.__init__(self, name, experiment, string)
        self.verbose = u'no'
        self.poll_time = 100


    def reset(self):

        """Resets plug-in to initial values."""
        pass


    def init_var(self):

        """Set en check variables."""

        if hasattr(self.experiment, "audio_low_latency_play_dummy_mode"):
            self.dummy_mode = self.experiment.audio_low_latency_play_dummy_mode
            self.verbose = self.experiment.audio_low_latency_play_verbose
        else:
            raise osexception(
                    u'Audio Low Latency Play Init item is missing')

        self.experiment.audio_low_latency_play_resume = 1


    def prepare(self):

        """Preparation phase"""

        # Call the parent constructor.
        item.prepare(self)

        self.init_var()

        # create keyboard object
        self.kb = keyboard(self.experiment,timeout=1)


    def run(self):

        """Run phase"""

        if not hasattr(self.experiment, "audio_low_latency_play_start"):
            raise osexception(
                    u'Audio Low Latency Play Start item is missing')

        self.set_item_onset()

        if self.dummy_mode == u'no':

            ## wait if thread has not started yet
            while not self.experiment.audio_low_latency_play_thread_running:
                self.clock.sleep(self.poll_time)

            ## send stop signal to thread
            self.show_message(u'Sending resume signal')
            self.experiment.audio_low_latency_play_execute_pause = 0

        elif self.dummy_mode == u'yes':
            self.show_message(u'Dummy mode enabled, NOT playing audio')
        else:
            self.show_message(u'Error with dummy mode!')


    def show_message(self, message):
        """
        desc:
            Show message.
        """

        debug.msg(message)
        if self.verbose == u'yes':
            print(message)


class qtaudio_low_latency_play_resume(audio_low_latency_play_resume, qtautoplugin):

    def __init__(self, name, experiment, script=None):

        """Plug-in GUI"""

        audio_low_latency_play_resume.__init__(self, name, experiment, script)
        qtautoplugin.__init__(self, __file__)
