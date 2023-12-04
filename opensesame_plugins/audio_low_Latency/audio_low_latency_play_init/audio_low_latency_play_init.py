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

import os
from libopensesame.py3compat import *
from libopensesame.item import Item
from libqtopensesame.items.qtautoplugin import QtAutoPlugin
from libopensesame.exceptions import OSException
from libopensesame.oslogging import oslogger
import pygame
import subprocess
import re

MODULES_ENABLED = ['alsaaudio', 'sounddevice', 'pyaudio']


class AudioLowLatencyPlayInit(Item):

    def reset(self):
        self.verbose = 'yes'
        self.var.dummy_mode = 'no'
        self.var.verbose = 'yes'
        self.var.bitdepth = 16
        self.var.samplerate = 44100
        self.var.channels = 2
        self.var.period_size = 1024
        self.var.periods = 4

        self.experiment.audio_low_latency_play_module_list = list()
        self.experiment.audio_low_latency_play_device_dict = dict()
        self.experiment.audio_low_latency_play_device_selected_dict = dict()

        self.pyalsaaudio_module_name = 'PyAlsaAudio (Linux only)'
        self.oss4_module_name = 'ossaudiodev (Linux only)'
        self.pyaudio_module_name = 'PyAudio (PortAudio)'
        self.sounddevice_module_name = 'SoundDevice (PortAudio)'

        self.experiment.pyalsaaudio_module_name = self.pyalsaaudio_module_name
        self.experiment.sounddevice_module_name = self.sounddevice_module_name
        self.experiment.pyaudio_module_name = self.pyaudio_module_name
        self.experiment.oss4_module_name = self.oss4_module_name

        if os.name == 'posix':
            if 'alsaaudio' in MODULES_ENABLED:
                try:
                    import alsaaudio
                    alsa_cards = alsaaudio.pcms(alsaaudio.PCM_PLAYBACK)
                    if alsa_cards:
                        self.experiment.audio_low_latency_play_module_list.append(self.pyalsaaudio_module_name)
                        self.experiment.audio_low_latency_play_device_dict[self.pyalsaaudio_module_name] = alsa_cards
                        self.experiment.audio_low_latency_play_device_selected_dict[self.pyalsaaudio_module_name] = alsa_cards[0]
                except ImportError:
                    self._show_message('Could not import alsaaudio')

            if 'ossaudiodev' in MODULES_ENABLED:
                try:
                    import ossaudiodev
                    self.experiment.audio_low_latency_play_module_list.append(self.oss4_module_name)
                    self.experiment.audio_low_latency_play_device_dict[self.oss4_module_name] = ['Exclusive Mode','Shared Mode']
                    self.experiment.audio_low_latency_play_device_selected_dict[self.oss4_module_name] = 'Exclusive Mode'
                except ImportError:
                    self._show_message('Could not import ossaudiodev')

        if 'sounddevice' in MODULES_ENABLED:
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

            except ImportError:
                self._show_message('Could not import sounddevice')

        if 'pyaudio' in MODULES_ENABLED:
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

            except ImportError:
                self._show_message('Could not import pyaudio')

        self._show_message('Audio Low Latency Play plug-in has been initialized!')

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

    def prepare(self):
        super().prepare()
        self._reset_device()
        self._init_var()

        if self.dummy_mode == 'no':
            self._show_message('\nChoosen playback parameters:\n')
            self._show_message('Module: %s' % self.module)
            self._show_message('Device: %s' % self.device_name)
            self._show_message('Bitdepth: %dbit' % self.bitdepth)
            self._show_message('Samplerate: %dHz' % self.samplerate)
            self._show_message('Channels: %d' % self.channels)
            self._show_message('Period size: %d frames' % self.period_size)
            self._show_message('Period time: %s ms' % str(self.period_time))
            if self.module == self.pyalsaaudio_module_name:
                self._show_message('Buffer size: %d frames' % self.buffer_size)
                self._show_message('Number of periods per buffer: %d' % self.periods)
            self._show_message('')

            try:
                pygame.mixer.stop()
                pygame.mixer.quit()
                self._show_message('Stopped pygame mixer')
            except:
                self._show_message('pygame mixer not active')

            if self.module == self.pyalsaaudio_module_name and self.pyalsaaudio_module_name in self.experiment.audio_low_latency_play_module_list:
                import alsaaudio
                self.device_index = self.experiment.audio_low_latency_play_device_dict[self.pyalsaaudio_module_name].index(self.device_name)

                error_msg_list = []

                if self.bitdepth == 8:
                    format_audio = alsaaudio.PCM_FORMAT_U8
                elif self.bitdepth == 16:
                    format_audio = alsaaudio.PCM_FORMAT_S16_LE
                elif self.bitdepth == 24:
                    format_audio = alsaaudio.PCM_FORMAT_S24_LE
                elif self.bitdepth == 32:
                    format_audio = alsaaudio.PCM_FORMAT_S32_LE
                else:
                    raise ValueError('Unsupported format')

                self.device = alsaaudio.PCM(type=alsaaudio.PCM_PLAYBACK,
                                            format=format_audio,
                                            device=self.device_name,
                                            channels=self.channels,
                                            rate=self.samplerate,
                                            periodsize=self.period_size,
                                            periods=self.periods)

                self._show_message('Audio device opened')

                device_info = self.device.info()

                reported_channels = device_info['channels']
                reported_rate = device_info['rate']
                reported_format_name = device_info['format_name']
                reported_period_size = device_info['period_size']
                reported_period_time = device_info['period_time']
                reported_periods = device_info['periods']

                real_period_time_round = round(reported_period_time / 1000, 1)

                # self._show_message('\nReported parameters:\n')
                # #self._show_message('Bitdepth: %dbit' % self.bitdepth)
                # self._show_message('Samplerate: %dHz' % reported_rate)
                # self._show_message('Channels: %d' % reported_channels)
                # self._show_message('Period size: %d frames' % reported_period_size)
                # self._show_message('Period time: %dms\n' % real_period_time_round)

                if reported_period_size != self.period_size:
                    error_msg_list.append('Period size of %d frames not supported. %d frames is recommended.\n' % (self.period_size, reported_period_size))
                if reported_periods != self.periods:
                    error_msg_list.append('Number of periods per buffer of %d not supported. factor of %d is recommended.\n' % (self.periods, reported_periods))
                if reported_channels != self.channels:
                    error_msg_list.append('%d channel(s) not supported. %d channel(s) is recommended.\n' % (self.channels, reported_channels))
                if reported_rate != self.samplerate:
                    error_msg_list.append('Samplerate of %d Hz not supported. %d Hz is recommended.\n\n' % (self.samplerate, reported_rate))
                # if reported_format_name != format_audio:
                #     error_msg_list.append('Audio format %s not supported. %s Hz is recommended.\n\n' % (format_audio, reported_format_name))
                if error_msg_list:
                    raise OSException('Error with device: %s\n%s' % (self.device_name, ''.join(error_msg_list)))

                error_msg_list = []

                pattern = "CARD=(.*?),"
                device_string = re.search(pattern, self.device_name)

                if device_string:
                    filename_alsa = '/proc/asound/'+device_string.group(1)+'/pcm0p/sub0/hw_params'
                    try:
                        real_buffer_size_string = subprocess.check_output(['grep', '-w', 'buffer_size', filename_alsa], text=True)
                        real_period_size_string = subprocess.check_output(['grep', '-w', 'period_size', filename_alsa], text=True)
                        real_channel_size_string = subprocess.check_output(['grep', '-w', 'channels', filename_alsa], text=True)
                        real_format_size_string = subprocess.check_output(['grep', '-w', 'format', filename_alsa], text=True)
                        real_samplerate_string = subprocess.check_output(['grep', '-w', 'rate', filename_alsa], text=True)

                        real_buffer_size_string = real_buffer_size_string.replace('\n','')
                        real_period_size_string = real_period_size_string.replace('\n','')
                        real_channel_size_string = real_channel_size_string.replace('\n','')
                        real_format_size_string = real_format_size_string.replace('\n','')
                        real_samplerate_string = real_samplerate_string.replace('\n','')

                        real_buffer_size = int(real_buffer_size_string.replace('buffer_size: ',''))
                        real_period_size = int(real_period_size_string.replace('period_size: ',''))
                        real_channel_size = int(real_channel_size_string.replace('channels: ',''))
                        real_format = real_format_size_string.replace('format: ','')

                        pattern_samplerate = "rate: (.*?) "
                        real_samplerate_string = re.search(pattern_samplerate, real_samplerate_string)
                        real_samplerate = int(real_samplerate_string.group(1))

                        real_periods = int(real_buffer_size / real_period_size)
                        real_period_time = round(float(real_period_size) / float(real_samplerate) * 1000, 1)

                        # self._show_message('\nHardware using parameters:\n')
                        # #self._show_message('Bitdepth: %dbit' % self.bitdepth)
                        # self._show_message('Samplerate: %dHz' % real_samplerate)
                        # self._show_message('Channels: %d' % real_channel_size)
                        # self._show_message('Period size: %d frames' % real_period_size)
                        # self._show_message('Period size time: %dms\n' % real_period_time)

                        if real_period_size != self.period_size:
                            error_msg_list.append('Period size of %d frames not supported. %d frames is recommended.\n' % (self.period_size, real_period_size))
                        else:
                            self._show_message('Chosen period size is supported and use is verified')
                        if real_periods != self.periods:
                            error_msg_list.append('%d periods per buffer not supported\n' % (self.periods))
                        if real_channel_size != self.channels:
                            error_msg_list.append('%d channel(s) not supported\n' % (self.channels))
                        if real_samplerate != self.samplerate:
                            error_msg_list.append('Samplerate of %d Hz not supported\n' % (self.samplerate))

                    except:
                        self._show_message('Could not verify parameters within Linux')
                        real_period_size = None
                else:
                    self._show_message('Could not verify parameters within Linux')
                    real_period_size = None

                if error_msg_list:
                    raise OSException('Error with device: %s\n%s' % (self.device_name, ''.join(error_msg_list)))

            elif self.module == self.pyaudio_module_name and self.pyaudio_module_name in self.experiment.audio_low_latency_play_module_list:
                import pyaudio
                self.device_index = self.experiment.audio_low_latency_play_device_dict[self.pyaudio_module_name].index(self.device_name)
                self.device_init = pyaudio.PyAudio()

                if self.bitdepth == 32:
                    raise OSException('%dbit audio not supported\n' % (self.bitdepth))
                else:
                    try:
                        self.device = self.device_init.open(format=self.device_init.get_format_from_width(self.samplewidth),
                                                            channels=self.channels,
                                                            rate=self.samplerate,
                                                            output=True,
                                                            frames_per_buffer=self.period_size,
                                                            output_device_index=self.device_index)

                        self._show_message("Audio device opened")

                    except Exception as e:
                        raise OSException('%dbit audio not supported\n\nMessage: %s' % (self.bitdepth, e))

                self._show_message('Estimated output latency: %fms ' % (self.device.get_output_latency()))
                self._show_message('Buffer size: %d frames ' % (self.device.get_write_available()))

            elif self.module == self.sounddevice_module_name and self.sounddevice_module_name in self.experiment.audio_low_latency_play_module_list:
                import sounddevice

                self.device_index = self.experiment.audio_low_latency_play_device_dict[self.sounddevice_module_name].index(self.device_name)

                if self.bitdepth == 8:
                    format_audio = 'uint8'
                elif self.bitdepth == 16:
                    format_audio = 'int16'
                elif self.bitdepth == 24:
                    format_audio = 'int24'
                elif self.bitdepth == 32:
                    format_audio = 'int32'
                else:
                    raise ValueError('Unsupported format')

                try:
                    self.device = sounddevice.RawOutputStream(samplerate=float(self.samplerate),
                                                              dtype=format_audio,
                                                              blocksize=int(self.period_size),
                                                              device=int(self.device_index),
                                                              channels=int(self.channels))
                    self._show_message("Audio device opened")
                except Exception as e:
                    raise OSException(
                        'Could not start audio device\n\nMessage: %s' % e)

                self.device.start()

            elif self.module == self.experiment.oss4_module_name:
                import ossaudiodev
                self.device = ossaudiodev.open('w')

                self._show_message("Audio device opened")

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
                    raise OSException('Device does not support %dbit audio\n\nMessage: %s' % (self.bitdepth, e))

                self.period_size = self.device.bufsize()
                self.period_time = round(float(self.period_size) / float(self.samplerate) * 1000, 1)
                self.data_size = int(self.frame_size * self.period_size / 8)

                self.experiment.audio_low_latency_play_period_size = self.period_size
                self.experiment.audio_low_latency_play_data_size = self.data_size
                self.experiment.var.audio_low_latency_play_period_size = self.period_size
                self.experiment.var.audio_low_latency_play_period_time = self.period_time

                self._show_message('Overruling period size with hardware buffer for OSS4, using: %d frames or %dms' % (self.period_size, self.period_time))

            self.experiment.audio_low_latency_play_device = self.device
            self.experiment.cleanup_functions.append(self.close)
        elif self.dummy_mode == 'yes':
            self.experiment.audio_low_latency_play_device = None
            self._show_message('Dummy mode enabled, run phase')
        else:
            self._show_message('Error with dummy mode, mode is: %s' % self.dummy_mode)

    def close(self):
        if not hasattr(self.experiment, "audio_low_latency_play_device") or \
            self.experiment.audio_low_latency_play_device is None:
            self._show_message("no active Audio Device")
            return
        try:
            self._show_message("Closing audio device")
            if self.module == self.pyaudio_module_name:
                self.experiment.audio_low_latency_play_device.stop_stream()
                self.experiment.audio_low_latency_play_device.close()
                self.device_init.terminate()
            else:
                self.experiment.audio_low_latency_play_device.close()
            self.experiment.audio_low_latency_play_device = None
            self._show_message("Audio device closed")
        except:
            self._show_message("failed to close Audio Device")

    def _init_var(self):
        self.dummy_mode = self.var.dummy_mode
        self.verbose = self.var.verbose
        self.module = self.var.module
        self.device_name = self.var.device_name

        if isinstance(self.var.period_size, int):
            self.period_size = self.var.period_size
        else:
            raise OSException('Period size value should be a integer')

        if isinstance(self.var.samplerate, int):
            self.samplerate = self.var.samplerate
        else:
            raise OSException('Sample rate value should be a integer')

        if isinstance(self.var.channels, int):
            self.channels = self.var.channels
        else:
            raise OSException('Channel value should be a integer')

        if isinstance(self.var.periods, int):
            self.periods = self.var.periods
        else:
            raise OSException('Number of periods per buffer value should be a integer')

        if isinstance(self.var.bitdepth, int):
            if self.var.bitdepth % 8 != 0:
                raise OSException('Bit depth should be a multiple of 8')
            else:
                self.bitdepth = self.var.bitdepth
                self.samplewidth = int(self.bitdepth / 8)
        else:
            raise OSException('Bit depth should be a integer')

        self.buffer_size = int(self.period_size * self.periods)
        self.frame_size = int(self.samplewidth * self.channels)
        self.data_size = int(self.frame_size * self.period_size)
        self.period_time = round(float(self.period_size) / float(self.samplerate) * 1000, 1)

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
        self.experiment.audio_low_latency_play_period_time = self.period_time
        if self.module == self.pyalsaaudio_module_name:
            self.experiment.audio_low_latency_play_buffer_size = self.buffer_size
            self.experiment.audio_low_latency_play_periods = self.periods
            self.experiment.audio_low_latency_play_buffer_time = round(self.periods * self.period_time, 1)

        self.experiment.var.audio_low_latency_play_module = self.module
        self.experiment.var.audio_low_latency_play_device_name = self.device_name
        self.experiment.var.audio_low_latency_play_period_size = self.period_size
        self.experiment.var.audio_low_latency_play_period_time = self.period_time
        if self.module == self.pyalsaaudio_module_name:
            self.experiment.var.audio_low_latency_play_buffer_size = self.buffer_size
            self.experiment.var.audio_low_latency_play_periods = self.periods
            self.experiment.var.audio_low_latency_play_buffer_time = self.experiment.audio_low_latency_play_buffer_time
        self.experiment.var.audio_low_latency_play_bitdepth = self.bitdepth
        self.experiment.var.audio_low_latency_play_samplewidth = self.samplewidth
        self.experiment.var.audio_low_latency_play_samplerate = self.samplerate
        self.experiment.var.audio_low_latency_play_channels = self.channels

        # reset experimental variables
        self.experiment.audio_low_latency_play_background = None
        # self.experiment.audio_low_latency_play_wait = None
        # self.experiment.audio_low_latency_play_stop = None
        # self.experiment.audio_low_latency_play_start = None
        # self.experiment.audio_low_latency_play_pause = None
        # self.experiment.audio_low_latency_play_resume = None

        self.experiment.audio_low_latency_play_thread_running = 0

    def _reset_device(self):
        if hasattr(self.experiment, 'audio_low_latency_play_device'):
            if self.experiment.audio_low_latency_play_device:
                self.experiment.audio_low_latency_play_device.close()

    def _show_message(self, message):
        oslogger.debug(message)
        if self.verbose == 'yes':
            print(message)


class QtAudioLowLatencyPlayInit(AudioLowLatencyPlayInit, QtAutoPlugin):

    def __init__(self, name, experiment, script=None):
        AudioLowLatencyPlayInit.__init__(self, name, experiment, script)
        QtAutoPlugin.__init__(self, __file__)

    def init_edit_widget(self):
        super().init_edit_widget()

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
        if not QtAutoPlugin.apply_edit_changes(self) or self.lock:
            return False
        self.custom_interactions()
        return True

    def edit_widget(self):
        if self.lock:
            return
        self.lock = True
        w = QtAutoPlugin.edit_widget(self)
        self.custom_interactions()
        self.lock = False
        return w

    def custom_interactions(self):
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

        if self.var.dummy_mode == 'yes':
            self.combobox_module.setDisabled(True)
            self.combobox_device_name.setDisabled(True)
        elif self.var.dummy_mode == 'no':
            self.combobox_module.setEnabled(True)
            self.combobox_device_name.setEnabled(True)

        if self.current_module == self.pyalsaaudio_module_name:
            self.line_edit_periods.setEnabled(True)
        else:
            self.line_edit_periods.setDisabled(True)

        if self.current_module == self.oss4_module_name:
            self.line_edit_period_size.setDisabled(True)
        else:
            self.line_edit_period_size.setEnabled(True)
