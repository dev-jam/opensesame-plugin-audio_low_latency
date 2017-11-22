#-*- coding:utf-8 -*-

"""
22-10-2017
Author: Bob Rosbag
Version: 2017.11-1

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

from libopensesame.py3compat import *
from libopensesame import debug
from libopensesame.item import item
from libqtopensesame.items.qtautoplugin import qtautoplugin
from libopensesame.exceptions import osexception
from openexp.keyboard import keyboard
import threading
import wave


VERSION = u'2017.11-1'

class audio_low_latency_play_start(item):

    """
    Class handles the basic functionality of the item.
    It does not deal with GUI stuff.
    """

    # Provide an informative description for your plug-in.
    description = u'Low Latency Audio: starts audio playback in the background.'

    def __init__(self, name, experiment, string=None):

        item.__init__(self, name, experiment, string)
        self.verbose = u'no'
        self.poll_time = 1


    def reset(self):

        """Resets plug-in to initial values."""

        # Set default experimental variables and values
        self.var.filename = u''
        self.var.duration = u'sound'
        self.var.delay = 0
        self.var.ram_cache = u'yes'


    def init_var(self):

        """Set en check variables."""

        if hasattr(self.experiment, "audio_low_latency_play_dummy_mode"):
            self.dummy_mode = self.experiment.audio_low_latency_play_dummy_mode
            self.verbose = self.experiment.audio_low_latency_play_verbose
            if self.dummy_mode == u'no':
                self.module = self.experiment.audio_low_latency_play_module
                self.device = self.experiment.audio_low_latency_play_device
                self.device_name = self.experiment.audio_low_latency_play_device_name
                self.device_index = self.experiment.audio_low_latency_play_device_index
                self.audio_buffer = self.experiment.audio_low_latency_play_buffer
        else:
            raise osexception(
                    u'Audio Low Latency Play Init item is missing')

        self.filename = self.experiment.pool[self.var.filename]
        self.ram_cache = self.var.ram_cache

        self.experiment.audio_low_latency_play_continue = 1
        self.experiment.audio_low_latency_play_start = 1


    def prepare(self):

        """Preparation phase"""

        # Call the parent constructor.
        item.prepare(self)

        # create keyboard object
        self.kb = keyboard(self.experiment,timeout=1)

        self.init_var()

        if self.dummy_mode == u'no':
            try:
                self.show_message(u'\n')
                self.show_message(u'Loading sound file: '+self.filename+' ...')
                self.wav_file = wave.open(self.filename, 'rb')
                self.show_message(u'Succesfully loaded sound file...')
            except Exception as e:
                raise osexception(
                    u'Could not load audio file', exception=e)

            self.buffer_time = round(float(self.audio_buffer) / float(self.wav_file.getframerate()) * 1000, 1)

            self.experiment.var.audio_low_latency_play_bitdepth = self.wav_file.getsampwidth()*8
            self.experiment.var.audio_low_latency_play_samplerate = self.wav_file.getframerate()
            self.experiment.var.audio_low_latency_play_channels = self.wav_file.getnchannels()
            self.experiment.var.audio_low_latency_play_buffer_time = self.buffer_time

            self.show_message(u'Bitdepth: ' +str(self.wav_file.getsampwidth()*8)+'bit')
            self.show_message(u'Samplerate: ' + str(self.wav_file.getframerate())+ 'Hz')
            self.show_message(u'Channels: ' + str(self.wav_file.getnchannels()))
            self.show_message(u'Buffer: ' + str(self.buffer_time)+'ms')

            self.frame_size = self.wav_file.getsampwidth() * 8 * self.wav_file.getnchannels()
            self.period_size = self.audio_buffer #* frame_size
            self.data_size = self.frame_size * self.period_size

            if self.module == self.experiment.pyalsaaudio_module_name:
                import alsaaudio
                self.device.close()
                self.device = alsaaudio.PCM(type=alsaaudio.PCM_PLAYBACK, device=self.device_name)
                self.experiment.audio_low_latency_play_device = self.device
                self.device.setchannels(self.wav_file.getnchannels())
                self.device.setrate(self.wav_file.getframerate())

                # 8bit is unsigned in wav files
                if self.wav_file.getsampwidth() == 1:
                    try:
                        self.device.setformat(alsaaudio.PCM_FORMAT_U8)
                    except Exception as e:
                        raise osexception(
                            u'Device does not support ' + str(self.wav_file.getsampwidth()*8) + u'bit audio', exception=e)
                # Otherwise we assume signed data, little endian
                elif self.wav_file.getsampwidth() == 2:
                    try:
                        self.device.setformat(alsaaudio.PCM_FORMAT_S16_LE)
                    except Exception as e:
                        raise osexception(
                            u'Device does not support ' + str(self.wav_file.getsampwidth()*8) + u'bit audio', exception=e)
                elif self.wav_file.getsampwidth() == 3:
                    raise osexception(
                        u'24bit will be supported in the next release')
#                    try:
#                        self.device.setformat(alsaaudio.PCM_FORMAT_S24_3LE)
#                    except Exception as e:
#                        raise osexception(
#                            u'Device does not support ' + str(self.wav_file.getsampwidth()*8) + u'bit audio', exception=e)
                elif self.wav_file.getsampwidth() == 4:
                    try:
                        self.device.setformat(alsaaudio.PCM_FORMAT_S32_LE)
                    except Exception as e:
                        raise osexception(
                            u'Device does not support ' + str(self.wav_file.getsampwidth()*8) + u'bit audio', exception=e)
                else:
                    raise ValueError('Unsupported format')

                self.device.setrate(self.wav_file.getframerate())
                self.device.setperiodsize(self.period_size)
                self.audio_stream = self.device
                self.experiment.audio_low_latency_play_stream = self.audio_stream
            elif self.module == self.experiment.pyaudio_module_name:
               if self.wav_file.getsampwidth() == 4:
                    raise osexception(
                        u'32bit not yet supported')
               else:
                    try:

                        if hasattr(self.experiment, "audio_low_latency_play_stream"):
                            self.experiment.audio_low_latency_play_stream.close()

                        self.audio_stream = self.device.open(format=self.device.get_format_from_width(self.wav_file.getsampwidth()),
                                channels=self.wav_file.getnchannels(),
                                rate=self.wav_file.getframerate(),
                                output=True,
                                frames_per_buffer=self.period_size,
                                output_device_index=self.device_index)
                        self.experiment.audio_low_latency_play_stream = self.audio_stream
                    except Exception as e:
                        raise osexception(
                            u'Could not start audio device', exception=e)

            if self.ram_cache == u'yes':
                wav_file_nframes = self.wav_file.getnframes()
                self.wav_file_data = self.wav_file.readframes(wav_file_nframes)
                self.wav_file.close()


    def run(self):

        """Run phase"""

        if not (hasattr(self.experiment, "audio_low_latency_play_stop") or hasattr(self.experiment, "audio_low_latency_play_wait")):
            raise osexception(
                    u'Audio Low Latency Play Stop or Audio Low Latency Play Wait item is missing')

        start_time = self.clock.time()

        error_msg = u'Duration must be a string named sound or a an integer greater than 1'

        if isinstance(self.var.duration,str):
            if self.var.duration == u'sound':
                self.duration_check = False
                self.duration = self.var.duration
            else:
                raise osexception(error_msg)
        elif isinstance(self.var.duration,int):
            if self.var.duration >= 1:
                self.duration_check = True
                self.duration = int(self.var.duration)
            else:
                raise osexception(error_msg)
        else:
            raise osexception(error_msg)

        if isinstance(self.var.delay,int):
            if self.var.delay >= 0:
                self.delay = int(self.var.delay)
                if self.delay > 0:
                    self.delay_check = True
                else:
                    self.delay_check = False
            else:
                raise osexception(u'Delay can not be negative')
        else:
            raise osexception(u'Delay should be a integer')

        self.set_item_onset()

        if self.dummy_mode == u'no':
            while self.experiment.audio_low_latency_play_locked:
                self.clock.sleep(self.poll_time)

            if self.delay_check:
                time_passed = self.clock.time() - start_time
                delay = self.delay - time_passed
            else:
                delay = self.delay


            self.show_message(u'Starting audio')
            self.experiment.audio_low_latency_play_locked = 1

            if self.ram_cache == u'no':
                self.experiment.audio_low_latency_play_thread = threading.Thread(target=self.play_file, args=(self.audio_stream, self.wav_file, self.period_size, delay))
            elif self.ram_cache == u'yes':
                self.experiment.audio_low_latency_play_thread = threading.Thread(target=self.play_data, args=(self.audio_stream, self.wav_file_data, self.data_size, delay))

            self.experiment.audio_low_latency_play_thread.start()

        elif self.dummy_mode == u'yes':
            self.show_message(u'Dummy mode enabled, NOT playing audio')
        else:
            raise osexception(u'Error with dummy mode!')


    def play_file(self, stream, wav_file, chunk, delay):

        self.experiment.audio_low_latency_play_thread_running = 1

        data = wav_file.readframes(chunk)

        if self.delay_check:
            if delay >= 1:
                self.clock.sleep(delay)

        self.experiment.var.audio_low_latency_play_start_onset = self.clock.time()
        start_time = self.clock.time()

        while len(data) > 0:
            # Read data from stdin
            stream.write(data)
            data = wav_file.readframes(chunk)

            if self.experiment.audio_low_latency_play_continue == 0:
                break
            elif self.duration_check:
                if self.clock.time() - start_time >= self.duration:
                    break

        if self.module == self.experiment.pyaudio_module_name:
            stream.stop_stream()  # stop stream

        wav_file.close()

        self.show_message(u'Stopped audio')
        self.experiment.audio_low_latency_play_locked = 0


    def play_data(self, stream, wav_data, chunk, delay):

        self.experiment.audio_low_latency_play_thread_running = 1

        if self.delay_check:
            if delay >= 1:
                self.clock.sleep(delay)

        self.experiment.var.audio_low_latency_play_start_onset = self.clock.time()
        start_time = self.clock.time()

        for start in range(0,len(wav_data),chunk):
            stream.write(wav_data[start:start+chunk])

            if self.experiment.audio_low_latency_play_continue == 0:
                break
            elif self.duration_check == u'yes':
                if self.clock.time() - start_time >= self.duration:
                    break

        if self.module == self.experiment.pyaudio_module_name:
            stream.stop_stream()  # stop stream

        self.show_message(u'Stopped audio')
        self.experiment.audio_low_latency_play_locked = 0


    def show_message(self, message):
        """
        desc:
            Show message.
        """

        debug.msg(message)
        if self.verbose == u'yes':
            print(message)


class qtaudio_low_latency_play_start(audio_low_latency_play_start, qtautoplugin):

    def __init__(self, name, experiment, script=None):

        """plug-in GUI"""

        audio_low_latency_play_start.__init__(self, name, experiment, script)
        qtautoplugin.__init__(self, __file__)
        self.text_version.setText(
        u'<small>Audio Low Latency version %s</small>' % VERSION)
