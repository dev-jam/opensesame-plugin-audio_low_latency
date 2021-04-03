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
import os

from libopensesame.py3compat import *
from libopensesame import debug
from libopensesame.item import item
from libqtopensesame.items.qtautoplugin import qtautoplugin
from libopensesame.exceptions import osexception
import pygame

VERSION = u'2021.03-1'

class audio_low_latency_play_init(item):

    """
    Class handles the basic functionality of the item.
    It does not deal with GUI stuff.
    """

    # Provide an informative description for your plug-in.
    description = u'Low Latency Audio: initializes the playback audio device.'
    lazy_init = False

    def __init__(self, name, experiment, string=None):

        self.verbose = u'no'
        self.modules_enabled = [u'alsaaudio', u'sounddevice', u'pyaudio']

        item.__init__(self, name, experiment, string)


    def reset(self):

        """Resets plug-in to initial values."""

        # Set default experimental variables and values
        self.var.dummy_mode = u'no'
        self.var.verbose = u'no'
        self.var.bitdepth = str(16)
        self.var.samplerate = str(44100)
        self.var.channels = str(2)
        self.var.period_size = 128

        self.experiment.audio_low_latency_play_module_list = list()
        self.experiment.audio_low_latency_play_device_dict = dict()
        self.experiment.audio_low_latency_play_device_selected_dict = dict()

        self.pyalsaaudio_module_name = u'PyAlsaAudio (Linux only)'
        self.oss4_module_name = u'ossaudiodev (Linux only)'
        self.pyaudio_module_name = u'PyAudio (PortAudio)'
        self.sounddevice_module_name = u'SoundDevice (PortAudio)'

        self.experiment.oss4_module_name = self.oss4_module_name
        self.experiment.pyalsaaudio_module_name = self.pyalsaaudio_module_name
        self.experiment.sounddevice_module_name = self.sounddevice_module_name
        self.experiment.pyaudio_module_name = self.pyaudio_module_name

        if os.name == 'posix':
            if u'alsaaudio' in self.modules_enabled:
                try:
                    import alsaaudio
                    alsa_cards = alsaaudio.pcms(alsaaudio.PCM_PLAYBACK)
                    if alsa_cards:
                        self.experiment.audio_low_latency_play_module_list.append(self.pyalsaaudio_module_name)
                        self.experiment.audio_low_latency_play_device_dict[self.pyalsaaudio_module_name] = alsa_cards
                        self.experiment.audio_low_latency_play_device_selected_dict[self.pyalsaaudio_module_name] = alsa_cards[0]
                except:
                    self.show_message(u'Could not import alsaaudio')

            if u'ossaudiodev' in self.modules_enabled:
                try:
                    import ossaudiodev
                    self.experiment.audio_low_latency_play_module_list.append(self.oss4_module_name)
                    self.experiment.audio_low_latency_play_device_dict[self.oss4_module_name] = [u'Exclusive Mode',u'Shared Mode']
                    self.experiment.audio_low_latency_play_device_selected_dict[self.oss4_module_name] = u'Exclusive Mode'
                except:
                    self.show_message(u'Could not import ossaudiodev')

        if u'sounddevice' in self.modules_enabled:
            try:
                import sounddevice
                sounddevice_cards = list()
                cards = sounddevice.query_devices()
                self.experiment.audio_low_latency_play_module_list.append(self.sounddevice_module_name)

                for di in range(0, len(cards)):
                    sounddevice_cards_dict = cards[di]
                    sounddevice_cards.append(sounddevice_cards_dict['name'])
                self.experiment.audio_low_latency_play_device_dict[self.sounddevice_module_name] = sounddevice_cards
                self.experiment.audio_low_latency_play_device_selected_dict[self.sounddevice_module_name] = sounddevice_cards[0]

            except:
                self.show_message(u'Could not import sounddevice')

        if u'pyaudio' in self.modules_enabled:
            try:
                import pyaudio
                pyaudio_cards = list()
                pyaudio_device = pyaudio.PyAudio()

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
        elif self.sounddevice_module_name in self.experiment.audio_low_latency_play_module_list:
            self.var.module = self.sounddevice_module_name
        elif self.pyaudio_module_name in self.experiment.audio_low_latency_play_module_list:
            self.var.module = self.pyaudio_module_name
        elif self.oss4_module_name in self.experiment.audio_low_latency_play_module_list:
            self.var.module = self.oss4_module_name

        device_list = self.experiment.audio_low_latency_play_device_dict[self.var.module]
        self.var.device_name = device_list[0]


    def init_var(self):

        """Set en check variables."""

        if hasattr(self.experiment, u'audio_low_latency_play_device'):
            if self.experiment.audio_low_latency_play_device:
                self.experiment.audio_low_latency_play_device.close()

        self.dummy_mode = self.var.dummy_mode
        self.verbose = self.var.verbose
        self.module = self.var.module
        self.device_name = self.var.device_name
        self.bitdepth = int(self.var.bitdepth)
        self.samplewidth = self.bitdepth // 8
        self.samplerate = int(self.var.samplerate)
        self.channels = int(self.var.channels)

        if isinstance(self.var.period_size,int):
            self.period_size = int(self.var.period_size)
        else:
            raise osexception(u'Period size value should be a integer')

        self.frame_size = self.bitdepth * self.channels
        self.data_size = self.frame_size * self.period_size
        self.period_size_time = round(float(self.period_size) / float(self.samplerate) * 1000, 1)

        self.experiment.audio_low_latency_play_dummy_mode = self.dummy_mode
        self.experiment.audio_low_latency_play_verbose = self.verbose
        self.experiment.audio_low_latency_play_locked = 0
        self.experiment.audio_low_latency_play_module = self.module
        self.experiment.audio_low_latency_play_bitdepth = self.bitdepth
        self.experiment.audio_low_latency_play_samplewidth = self.samplewidth
        self.experiment.audio_low_latency_play_samplerate = self.samplerate
        self.experiment.audio_low_latency_play_channels = self.channels
        self.experiment.audio_low_latency_play_period_size = self.period_size
        self.experiment.audio_low_latency_play_data_size = self.data_size
        self.experiment.audio_low_latency_play_period_size_time = self.period_size_time

        self.experiment.var.audio_low_latency_play_module = self.module
        self.experiment.var.audio_low_latency_play_device_name = self.device_name
        self.experiment.var.audio_low_latency_play_period_size = self.period_size
        self.experiment.var.audio_low_latency_play_bitdepth = self.bitdepth
        self.experiment.var.audio_low_latency_play_samplewidth = self.samplewidth
        self.experiment.var.audio_low_latency_play_samplerate = self.samplerate
        self.experiment.var.audio_low_latency_play_channels = self.channels

        # reset experimental variables
        self.experiment.audio_low_latency_play_wait = None
        self.experiment.audio_low_latency_play_stop = None
        self.experiment.audio_low_latency_play_start = None
        self.experiment.audio_low_latency_play_pause = None
        self.experiment.audio_low_latency_play_resume = None

        self.experiment.audio_low_latency_play_thread_running = 0

    def prepare(self):

        """Preparation phase"""

        # Call the parent constructor.
        item.prepare(self)
        self.close()
        self.init_var()

        if self.dummy_mode == u'no':

            self.show_message(u'Module: ' + self.module)
            self.show_message(u'Device: ' + self.device_name)
            self.show_message(u'Bitdepth: ' + str(self.bitdepth)+'bit')
            self.show_message(u'Samplerate: ' + str(self.samplerate) + 'Hz')
            self.show_message(u'Channels: ' + str(self.channels))
            self.show_message(u'Period size time: ' + str(self.period_size_time)+'ms')

            try:
                # disable the internal audio device / mixer
                pygame.mixer.stop()
                pygame.mixer.quit()
                self.show_message(u'Stopped pygame mixer')
            except:
                self.show_message(u'pygame mixer not active')

            if self.module == self.pyalsaaudio_module_name and self.pyalsaaudio_module_name in self.experiment.audio_low_latency_play_module_list:
                import alsaaudio
                self.device_index = self.experiment.audio_low_latency_play_device_dict[self.pyalsaaudio_module_name].index(self.device_name)

                # self.device = alsaaudio.PCM(type=alsaaudio.PCM_PLAYBACK,
                #                             device=self.device_name,
                #                             channels=self.channels,
                #                             rate=self.samplerate,
                #                             periodsize=self.period_size)

                self.device = alsaaudio.PCM(type=alsaaudio.PCM_PLAYBACK, device=self.device_name)

                channels_set = self.device.setchannels(self.channels)
                samplerate_set = self.device.setrate(self.samplerate)
                period_size_set = self.device.setperiodsize(self.period_size)

                error_msg_list = []
                error_msg_bitdepth = u'%dbit audio not supported\n' % (self.bitdepth)

                if self.bitdepth == 8:
                    format_audio = alsaaudio.PCM_FORMAT_U8
                elif self.bitdepth == 16:
                    format_audio = alsaaudio.PCM_FORMAT_S16_LE
                elif self.bitdepth == 24:
                    error_msg_list.append(error_msg_bitdepth)
                elif self.bitdepth == 32:
                    format_audio = alsaaudio.PCM_FORMAT_S32_LE
                else:
                    raise ValueError('Unsupported format')

                try:
                    self.device.setformat(format_audio)
                except Exception as e:
                    error_msg_list.append(error_msg_bitdepth)

                if channels_set != self.channels:
                    error_msg_list.append(u'%d channel(s) not supported\n' % (self.channels))
                if samplerate_set != self.samplerate:
                    error_msg_list.append(u'Samplerate of %d Hz not supported\n' % (self.samplerate))
                if period_size_set != self.period_size:
                    error_msg_list.append(u'Period size of %d frames not supported. %d frames is recommended.\n' % (self.period_size, period_size_set))
                if error_msg_list:
                    raise osexception(u'Error with device: %s\n%s' % (self.device_name, ''.join(error_msg_list)))


            elif self.module == self.pyaudio_module_name and self.pyaudio_module_name in self.experiment.audio_low_latency_play_module_list:
                import pyaudio
                self.device_index = self.experiment.audio_low_latency_play_device_dict[self.pyaudio_module_name].index(self.device_name)
                self.device_init = pyaudio.PyAudio()

                if self.bitdepth == 32:
                    raise osexception(u'%dbit audio not supported\n' % (self.bitdepth))
                else:
                    try:
                        self.device = self.device_init.open(format=self.device_init.get_format_from_width(self.samplewidth),
                                channels=self.channels,
                                rate=self.samplerate,
                                output=True,
                                frames_per_buffer=self.period_size,
                                output_device_index=self.device_index)

                    except Exception as e:
                        raise osexception(u'%dbit audio not supported\n' % (self.bitdepth), exception=e)

                self.show_message(u'Estimated output latency: %fms ' % (self.device.get_output_latency()))
                self.show_message(u'Buffer size: %d frames ' % (self.device.get_write_available()))

            elif self.module == self.sounddevice_module_name and self.sounddevice_module_name in self.experiment.audio_low_latency_play_module_list:
                import sounddevice

                self.device_index = self.experiment.audio_low_latency_play_device_dict[self.sounddevice_module_name].index(self.device_name)

                if self.bitdepth == 8:
                    format_audio = u'uint8'
                elif self.bitdepth == 16:
                    format_audio = u'int16'
                elif self.bitdepth == 24:
                    format_audio = u'int24'
                elif self.bitdepth == 32:
                    format_audio = u'int32'
                else:
                    raise ValueError('Unsupported format')

                try:

                    self.device = sounddevice.RawOutputStream(samplerate=float(self.samplerate),
                                                              dtype=format_audio,
                                                              blocksize=int(self.period_size),
                                                              device=int(self.device_index),
                                                              channels=int(self.channels))

                except Exception as e:
                    raise osexception(
                        u'Could not start audio device', exception=e)

            elif self.module == self.experiment.oss4_module_name:
                import ossaudiodev
                self.device = ossaudiodev.open('w')
                self.device.channels(self.channels)
                self.device.speed(self.samplerate)

                if self.bitdepth == 8:
                    format_audio = ossaudiodev.AFMT_U8
                elif self.bitdepth == 16:
                    format_audio = ossaudiodev.AFMT_S16_LE
                else:
                    raise ValueError('Unsupported format')

                try:
                    self.device.setfmt(format_audio)
                except Exception as e:
                    raise osexception(
                        u'Device does not support ' + str(self.bitdepth) + u'bit audio', exception=e)

                self.period_size = self.device.bufsize()
                self.period_size_time = round(float(self.period_size) / float(self.samplerate) * 1000, 1)
                self.data_size = self.frame_size * self.period_size

                self.experiment.audio_low_latency_play_period_size = self.period_size
                self.experiment.audio_low_latency_play_data_size = self.data_size
                self.experiment.var.audio_low_latency_play_period_size = self.period_size

                print('Overruling period size with hardware buffer for OSS4, using: ' + str(self.period_size) + ' frames or ' + str(self.period_size_time) + 'ms')

            self.experiment.audio_low_latency_play_device = self.device
            #self.experiment.cleanup_functions.append(self.close)
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
            self.device.close()
            if  self.module == self.pyaudio_module_name:
                self.device.terminate()
            self.device = None
            self.experiment.audio_low_latency_play_device = None
            self.show_message(u"Audio device closed")
        except:
            self.show_message(u"failed to close Audio Device")


class qtaudio_low_latency_play_init(audio_low_latency_play_init, qtautoplugin):

    def __init__(self, name, experiment, script=None):

        """plug-in GUI"""

        audio_low_latency_play_init.__init__(self, name, experiment, script)
        qtautoplugin.__init__(self, __file__)

        if self.var.module in self.experiment.audio_low_latency_play_module_list:
            self.current_module = self.var.module
        else:
            self.current_module = self.experiment.audio_low_latency_play_module_list[0]
            self.var.module = self.current_module

        if self.var.device_name in self.experiment.audio_low_latency_play_device_dict[self.current_module]:
            self.current_device_name = self.var.device_name
        else:
            device_list = self.experiment.audio_low_latency_play_device_dict[self.current_module]
            self.current_device_name = device_list[0]
            self.experiment.audio_low_latency_play_device_selected_dict[self.current_module] = self.current_device_name
            self.var.device_name = self.current_device_name

        device_index = self.experiment.audio_low_latency_play_device_dict[self.current_module].index(self.current_device_name)

        self.combobox_module.clear()
        self.combobox_module.addItems(self.experiment.audio_low_latency_play_module_list)
        self.combobox_module.setCurrentIndex(self.experiment.audio_low_latency_play_module_list.index(self.current_module))

        self.combobox_device_name.clear()
        self.combobox_device_name.addItems(self.experiment.audio_low_latency_play_device_dict[self.current_module])
        self.combobox_device_name.setCurrentIndex(device_index)

    def apply_edit_changes(self):

        """
        desc:
            Applies the controls.
        """

        if not qtautoplugin.apply_edit_changes(self) or self.lock:
            return False
        self.custom_interactions()
        return True

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
            old_device_name = self.var.device_name
            self.experiment.audio_low_latency_play_device_selected_dict[self.current_module] = old_device_name

            new_module_name = self.var.module
            new_device_name = self.experiment.audio_low_latency_play_device_selected_dict[new_module_name]
            new_device_index = self.experiment.audio_low_latency_play_device_dict[new_module_name].index(new_device_name)

            self.combobox_device_name.clear()
            self.combobox_device_name.addItems(self.experiment.audio_low_latency_play_device_dict[new_module_name])
            self.combobox_device_name.setCurrentIndex(new_device_index)

            self.current_module = new_module_name
            self.current_device_name = new_device_name
            self.var.device_name = self.current_device_name

        if self.var.dummy_mode == u'yes':
            self.combobox_module.setDisabled(True)
            self.combobox_device_name.setDisabled(True)
        elif self.var.dummy_mode == u'no':
            self.combobox_module.setEnabled(True)
            self.combobox_device_name.setEnabled(True)

        if self.current_module == self.oss4_module_name:
            self.line_edit_period_size.setDisabled(True)
        else:
            self.line_edit_period_size.setEnabled(True)
