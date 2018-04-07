#-*- coding:utf-8 -*-

"""
Author: Bob Rosbag
2017

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
import threading
import wave

VERSION = u'2018.04-2'

class audio_low_latency_record_start(item):

    """
    Class handles the basic functionality of the item.
    It does not deal with GUI stuff.
    """

    # Provide an informative description for your plug-in.
    description = u'Low Latency Audio: starts audio recording in the background.'

    def __init__(self, name, experiment, string=None):

        item.__init__(self, name, experiment, string)
        self.verbose = u'no'
        self.poll_time = 10


    def reset(self):

        """Resets plug-in to initial values."""

        # Set default experimental variables and values
        self.var.filename = u''
        self.var.duration = u'infinite'
        self.var.delay = 0
        self.var.bitdepth = str(16)
        self.var.samplerate = str(44100)
        self.var.channels = str(1)
        self.var.ram_cache = u'yes'


    def init_var(self):

        """Set en check variables."""

        if hasattr(self.experiment, "audio_low_latency_record_dummy_mode"):
            self.dummy_mode = self.experiment.audio_low_latency_record_dummy_mode
            self.verbose = self.experiment.audio_low_latency_record_verbose
            if self.dummy_mode == u'no':
                self.module = self.experiment.audio_low_latency_record_module
                self.device = self.experiment.audio_low_latency_record_device
            self.period_size = self.experiment.audio_low_latency_record_period_size
            self.period_size_time = self.experiment.audio_low_latency_record_period_size_time
            self.data_size = self.experiment.audio_low_latency_record_data_size
            self.bitdepth = self.experiment.audio_low_latency_record_bitdepth
            self.samplewidth = self.experiment.audio_low_latency_record_samplewidth
            self.samplerate = self.experiment.audio_low_latency_record_samplerate
            self.channels = self.experiment.audio_low_latency_record_channels

        else:
            raise osexception(
                    u'Audio Low Latency Record Init item is missing')

        self.filename = self.var.filename
        self.ram_cache = self.var.ram_cache

        self.experiment.audio_low_latency_record_continue = 1
        self.experiment.audio_low_latency_record_start = 1


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
                self.show_message(u'Creating wave file: '+self.filename+' ...')
                self.wav_file = wave.open(self.filename, 'wb')
                self.show_message(u'Succesfully created wave file...')
            except Exception as e:
                raise osexception(
                    u'Could not create wave file', exception=e)

            self.wav_file.setsampwidth(self.samplewidth)
            self.wav_file.setframerate(self.samplerate)
            self.wav_file.setnchannels(self.channels)

            self.show_message(u'Period size: %d frames' % (self.period_size))
            self.show_message(u'Period duration: %s ms' % (str(self.period_size_time)))


    def run(self):

        """Run phase"""

        self.set_item_onset()

        if not (hasattr(self.experiment, "audio_low_latency_record_stop") or hasattr(self.experiment, "audio_low_latency_record_wait")):
            raise osexception(
                    u'Audio Low Latency Record Stop or Audio Low Latency Record Wait item is missing')

        start_time = self.clock.time()

        error_msg = u'Duration must be a string named infinite or a an integer greater than 1'

        if isinstance(self.var.duration,str):
            if self.var.duration == u'infinite':
                self.duration_check = False
                self.duration = self.var.duration
            else:
                raise osexception(error_msg)
        elif isinstance(self.var.duration,int):
            if self.var.duration >= 1:
                self.duration_check = True
                self.duration = int(self.var.duration)
                if self.duration < self.period_size_time:
                    raise osexception(u'Duration should be larger than period duration')
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

        if self.dummy_mode == u'no':
            while self.experiment.audio_low_latency_record_locked:
                self.clock.sleep(self.poll_time)

            if self.delay_check:
                time_passed = self.clock.time() - start_time
                delay = self.delay - time_passed
            else:
                delay = self.delay

            self.show_message(u'Starting recording audio')
            self.experiment.audio_low_latency_record_locked = 1
            self.experiment.audio_low_latency_record_thread = threading.Thread(target=self.record, args=(self.device, self.wav_file, self.period_size, delay))
            self.experiment.audio_low_latency_record_thread.start()
        elif self.dummy_mode == u'yes':
            self.show_message(u'Dummy mode enabled, NOT recording audio')
        else:
            raise osexception(u'Error with dummy mode!')


    def record(self, stream, wav_file, chunk, delay):

        self.experiment.audio_low_latency_record_thread_running = 1

        frames = []

        if self.delay_check:
            if delay >= 1:
                self.clock.sleep(delay)

        self.set_stimulus_onset()
        start_time = self.clock.time()

        if self.module == self.experiment.sounddevice_module_name:
            stream.start()
        elif self.module == self.experiment.pyaudio_module_name:
            stream.start_stream()

        while True:

            # Read data from device
            if self.module == self.experiment.pyalsaaudio_module_name:
                l, data = stream.read()
            else:
                data = stream.read(chunk)

            # save data to file/ram
            if self.ram_cache == u'yes':
                frames.append(data)
            elif self.ram_cache == u'no':
                wav_file.writeframes(data)

            # check for stop
            if self.experiment.audio_low_latency_record_continue == 0:
                break
            elif self.duration_check:
                if self.clock.time() - start_time >= self.duration:
                    break

        self.set_stimulus_offset()

        if self.ram_cache == u'yes':
            wav_file.writeframes(b''.join(frames))

        if self.module == self.experiment.sounddevice_module_name:
            stream.stop()
        elif self.module == self.experiment.pyaudio_module_name:
            stream.stop_stream()

        wav_file.close()

        self.show_message(u'Stopped recording audio')
        self.experiment.audio_low_latency_record_locked = 0


    def show_message(self, message):
        """
        desc:
            Show message.
        """

        debug.msg(message)
        if self.verbose == u'yes':
            print(message)


    def set_stimulus_onset(self, time=None):

        """
        desc:
            Set a timestamp for the onset time of the item's execution.

        keywords:
            time:    A timestamp or None to use the current time.

        returns:
            desc:    A timestamp.
        """

        if time is None:
            time = self.clock.time()
        self.experiment.var.set(u'time_stimulus_onset_%s' % self.name, time)
        return time


    def set_stimulus_offset(self, time=None):

        """
        desc:
            Set a timestamp for the onset time of the item's execution.

        keywords:
            time:    A timestamp or None to use the current time.

        returns:
            desc:    A timestamp.
        """

        if time is None:
            time = self.clock.time()
        self.experiment.var.set(u'time_stimulus_offset_%s' % self.name, time)
        return time


    def set_stimulus_timing(self, _type, time=None):

        """
        desc:
            Set a timestamp for the onset time of the item's execution.

        keywords:
            time:    A timestamp or None to use the current time.

        returns:
            desc:    A timestamp.
        """

        if time is None:
            time = self.clock.time()
        self.experiment.var.set(u'time_stimulus_%s_%s' % (_type, self.name), time)
        return time


class qtaudio_low_latency_record_start(audio_low_latency_record_start, qtautoplugin):

    def __init__(self, name, experiment, script=None):

        """plug-in GUI"""

        audio_low_latency_record_start.__init__(self, name, experiment, script)
        qtautoplugin.__init__(self, __file__)
        self.text_version.setText(
        u'<small>Audio Low Latency version %s</small>' % VERSION)

