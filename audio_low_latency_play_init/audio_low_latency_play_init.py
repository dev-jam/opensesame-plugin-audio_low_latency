#-*- coding:utf-8 -*-

"""
22-10-2017
Author: Bob Rosbag
Version: 0.9

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

#import warnings
import os

from libopensesame.py3compat import *
from libopensesame import debug
from libopensesame.item import item
from libqtopensesame.items.qtautoplugin import qtautoplugin
from libopensesame.exceptions import osexception
import pygame

VERSION = u'2017.11-1'

class audio_low_latency_play_init(item):

    """
    Class handles the basic functionality of the item.
    It does not deal with GUI stuff.
    """

    # Provide an informative description for your plug-in.
    description = u'Low Latency Audio: initializes the playback audio device.'

    def __init__(self, name, experiment, string=None):

        item.__init__(self, name, experiment, string)
        self.verbose = u'no'


    def reset(self):

        """Resets plug-in to initial values."""

        # Set default experimental variables and values
        self.var.dummy_mode = u'no'
        self.var.verbose = u'no'
        self.var.audio_buffer = 1024

        self.experiment.audio_low_latency_play_module_list = list()
        self.experiment.audio_low_latency_play_device_dict = dict()
        self.experiment.audio_low_latency_play_device_selected_dict = dict()

        self.pyalsaaudio_module_name = u'PyAlsaAudio (Low Latency)'
        self.pyaudio_module_name = u'PyAudio (Compatibility)'


        if os.name == 'posix':
            try:
                import alsaaudio
                alsa_cards = alsaaudio.pcms(alsaaudio.PCM_PLAYBACK)
                self.experiment.pyalsaaudio_module_name = self.pyalsaaudio_module_name
                if alsa_cards:
                    self.experiment.audio_low_latency_play_module_list.append(self.pyalsaaudio_module_name)
                    self.experiment.audio_low_latency_play_device_dict[self.pyalsaaudio_module_name] = alsa_cards
                    self.experiment.audio_low_latency_play_device_selected_dict[self.pyalsaaudio_module_name] = alsa_cards[0]
            except:
                self.show_message(u'Could not import alsaaudio')

        try:
            import pyaudio

            pyaudio_cards = list()
            pyaudio_device = pyaudio.PyAudio()
            self.experiment.pyaudio_module_name = self.pyaudio_module_name
            self.experiment.audio_low_latency_play_module_list.append(self.pyaudio_module_name)

            for di in range(0, pyaudio_device.get_device_count()):
                pyaudio_cards_dict = pyaudio_device.get_device_info_by_index(di)
                pyaudio_cards.append(pyaudio_cards_dict['name'])

            self.experiment.audio_low_latency_play_device_dict[self.pyaudio_module_name] = pyaudio_cards
            self.experiment.audio_low_latency_play_device_selected_dict[self.pyaudio_module_name] = pyaudio_cards[0]

        except:
            self.show_message(u'Could not import pyaudio')

        self.show_message(u'Audio Low Latency Play plug-in has been initialized!')


        if self.pyalsaaudio_module_name in self.experiment.audio_low_latency_play_module_list:
            self.var.module = self.pyalsaaudio_module_name

            #self.var.device = self.experiment.device_dict[u'PyAlsaAudio (Low Latency)']
        elif self.pyaudio_module_name in self.experiment.audio_low_latency_play_module_list:
            self.var.module = self.pyaudio_module_name

        self.current_module = self.var.module
        device_list = self.experiment.audio_low_latency_play_device_dict[self.current_module]
        self.current_device = device_list[0]
        self.var.device = self.current_device


    def init_var(self):

        """Set en check variables."""

        if hasattr(self.experiment, u'audio_low_latency_play_device'):
            raise osexception(
                u'You should have only one instance of `Audio Low Latency Play Init` in your experiment')

        self.dummy_mode = self.var.dummy_mode
        self.verbose = self.var.verbose
        self.module = self.var.module
        self.device = self.var.device

        if isinstance(self.var.audio_buffer,int):
            self.experiment.audio_low_latency_play_buffer = int(self.var.audio_buffer)
        else:
            raise osexception(u'Buffer value should be a integer')

        self.experiment.audio_low_latency_play_dummy_mode = self.var.dummy_mode
        self.experiment.audio_low_latency_play_verbose = self.var.verbose
        self.experiment.audio_low_latency_play_locked = 0
        self.experiment.audio_low_latency_play_module = self.var.module

        self.experiment.var.audio_low_latency_play_module = self.var.module
        self.experiment.var.audio_low_latency_play_device_name = self.var.device
        self.experiment.var.audio_low_latency_play_buffer = int(self.var.audio_buffer)

        # reset experimental variables
        self.experiment.audio_low_latency_play_wait = None
        self.experiment.audio_low_latency_play_stop = None
        self.experiment.audio_low_latency_play_start = None

        self.experiment.audio_low_latency_play_thread_running = 0

    def prepare(self):

        """Preparation phase"""

        # Call the parent constructor.
        item.prepare(self)
        self.close()
        self.init_var()

        if self.dummy_mode == u'no':

            # disable the internal audio device / mixer
            pygame.mixer.stop()
            pygame.mixer.quit()

            if not hasattr(self.experiment, "audio_low_latency_play_device"):
                if self.module == self.pyalsaaudio_module_name and self.pyalsaaudio_module_name in self.experiment.audio_low_latency_play_module_list:
                    import alsaaudio
                    self.experiment.audio_low_latency_play_device_index = self.experiment.audio_low_latency_play_device_dict[self.pyalsaaudio_module_name].index(self.device)
                    self.experiment.audio_low_latency_play_device = alsaaudio.PCM(type=alsaaudio.PCM_PLAYBACK, device=self.device)
                elif self.module == self.pyaudio_module_name and self.pyaudio_module_name in self.experiment.audio_low_latency_play_module_list:
                    import pyaudio
                    self.experiment.audio_low_latency_play_device_index = self.experiment.audio_low_latency_play_device_dict[self.pyaudio_module_name].index(self.device)
                    self.experiment.audio_low_latency_play_device = pyaudio.PyAudio()
                self.experiment.cleanup_functions.append(self.close)
                self.python_workspace[u'audio_low_latency_play'] = self.experiment.audio_low_latency_play_device

        elif self.dummy_mode == u'yes':
            self.show_message(u'Dummy mode enabled, run phase')
        else:
            self.show_message(u'Error with dummy mode, mode is: %s' % self.dummy_mode)


    def run(self):

        """Run phase"""

        self.set_item_onset()


    def show_message(self, message):
        """
        desc:
            Show message.
        """

        debug.msg(message)
        if self.verbose == u'yes':
            print(message)


    def close(self):

        """
        desc:
            Neatly close the connection to the parallel port.
        """

        if not hasattr(self.experiment, "audio_low_latency_play_device") or \
            self.experiment.audio_low_latency_play_device is None:
                self.show_message(u"no active Audio Device")
                return
        try:
            self.show_message(u"Closing audio device")
            self.experiment.audio_low_latency_play_device.close()
            if  self.module == u'PyAudio (Compatibility)':
                self.experiment.audio_low_latency_play_device.terminate()
            self.experiment.audio_low_latency_play_device = None
            self.show_message(u"Audio device closed")
        except:
            self.show_message(u"failed to close Audio Device")


class qtaudio_low_latency_play_init(audio_low_latency_play_init, qtautoplugin):

    def __init__(self, name, experiment, script=None):

        """plug-in GUI"""

        audio_low_latency_play_init.__init__(self, name, experiment, script)
        qtautoplugin.__init__(self, __file__)
        self.text_version.setText(
        u'<small>Audio Low Latency version %s</small>' % VERSION)

        self.combobox_module.clear()
        self.combobox_module.addItems(self.experiment.audio_low_latency_play_module_list)
        self.combobox_module.setCurrentIndex(self.experiment.audio_low_latency_play_module_list.index(self.var.module))

        self.combobox_device.clear()
        self.combobox_device.addItems(self.experiment.audio_low_latency_play_device_dict[self.current_module])

        device_name = self.experiment.audio_low_latency_play_device_selected_dict[self.current_module]
        device_index = self.experiment.audio_low_latency_play_device_dict[self.current_module].index(device_name)
        self.combobox_device.setCurrentIndex(device_index)

    def apply_edit_changes(self):

        """
        desc:
            Applies the controls.
        """

        if not qtautoplugin.apply_edit_changes(self) or self.lock:
            return False
        self.custom_interactions()


    def edit_widget(self):

        """
        Refreshes the controls.

        Returns:
        The QWidget containing the controls
        """

        if self.lock:
            return
        self.lock = True
        w = qtautoplugin.edit_widget(self)
        self.custom_interactions()
        self.lock = False
        return w

    def custom_interactions(self):

        """
        desc:
            Activates the relevant controls for each tracker.
        """

        if self.current_module != self.var.module:
            ## save old device
            old_device = self.var.device
            self.experiment.audio_low_latency_play_device_selected_dict[self.current_module] = old_device

            new_module_name = self.var.module
            self.combobox_device.clear()
            self.combobox_device.addItems(self.experiment.audio_low_latency_play_device_dict[new_module_name])

            new_device_name = self.experiment.audio_low_latency_play_device_selected_dict[new_module_name]
            new_device_index = self.experiment.audio_low_latency_play_device_dict[new_module_name].index(new_device_name)
            self.combobox_device.setCurrentIndex(new_device_index)

            self.current_module = new_module_name
            self.var.device = new_device_name

        if self.var.dummy_mode == u'yes':
            self.combobox_module.setDisabled(True)
            self.combobox_device.setDisabled(True)
        elif self.var.dummy_mode == u'no':
            self.combobox_module.setEnabled(True)
            self.combobox_device.setEnabled(True)
