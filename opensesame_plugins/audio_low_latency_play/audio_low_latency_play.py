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
import wave

VERSION = u'2020.1-1'

class audio_low_latency_play(item):

    """
    Class handles the basic functionality of the item.
    It does not deal with GUI stuff.
    """

    # Provide an informative description for your plug-in.
    description = u'Low Latency Audio: starts audio playback on the foreground.'

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
            self.period_size = self.experiment.audio_low_latency_play_period_size
            self.period_size_time = self.experiment.audio_low_latency_play_period_size_time
            self.data_size = self.experiment.audio_low_latency_play_data_size
            self.bitdepth = self.experiment.audio_low_latency_play_bitdepth
            self.samplewidth = self.experiment.audio_low_latency_play_samplewidth
            self.samplerate = self.experiment.audio_low_latency_play_samplerate
            self.channels = self.experiment.audio_low_latency_play_channels
        else:
            raise osexception(
                    u'Audio Low Latency Play Init item is missing')

        self.filename = self.experiment.pool[self.var.filename]
        self.ram_cache = self.var.ram_cache


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

            self.wav_duration = int(round(float(self.wav_file.getnframes()) / float(self.wav_file.getframerate()) * 1000, 1))
            self.show_message(u'Audio file duration: %d ms' % (self.wav_duration))
            self.show_message(u'Period size: %d frames' % (self.period_size))
            self.show_message(u'Period duration: %s ms' % (str(self.period_size_time)))

            error_msg_list = []

            if self.wav_file.getsampwidth() * 8 != self.bitdepth:
                error_msg_list.append(u'- bitdepth incorrect, file is %dbit but experiment is set to %dbit\n' % (self.wav_file.getsampwidth()*8,self.bitdepth))
                #raise osexception(u'wave file has incorrect bitdepth')
            if self.wav_file.getframerate() != self.samplerate:
                error_msg_list.append(u'- samplerate incorrect, file is %dHz but experiment is set to %dHz\n' % (self.wav_file.getframerate(),self.samplerate))
                #raise osexception(u'wave file has incorrect samplerate')
            if self.wav_file.getnchannels() != self.channels:
                error_msg_list.append(u'- number of channels incorrect, file has %d channel(s) but experiment is set to %d channel(s)\n' % (self.wav_file.getnchannels(), self.channels))
                #raise osexception(u'wave file has incorrect number of channels')
            if self.wav_file.getnframes() < self.period_size:
                error_msg_list.append(u'- Period size is larger than total number of frames in wave file, use a period size smaller than %d frames\n' % (self.wav_file.getnframes()))
            if error_msg_list:
                raise osexception(u'Error with audio file %s\n%s' % (self.filename, ''.join(error_msg_list)))

            if self.ram_cache == u'yes':
                wav_file_nframes = self.wav_file.getnframes()
                self.wav_file_data = self.wav_file.readframes(wav_file_nframes)
                self.wav_file.close()


    def run(self):

        """Run phase"""

        self.set_item_onset()

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

        if self.dummy_mode == u'no':
            while self.experiment.audio_low_latency_play_locked:
                self.clock.sleep(self.poll_time)

            if self.delay_check:
                time_passed = self.clock.time() - start_time
                delay = self.delay - time_passed
            else:
                delay = self.delay

            self.show_message(u'Starting audio')

            if self.ram_cache == u'No':
                self.play_file(self.device, self.wav_file, self.period_size, delay)
            elif self.ram_cache == u'yes':
                self.play_data(self.device, self.wav_file_data, self.data_size, delay)


        elif self.dummy_mode == u'yes':
            self.set_stimulus_onset()
            self.show_message(u'Dummy mode enabled, NOT playing audio')
        else:
            raise osexception(u'Error with dummy mode!')


    def play_file(self, stream, wav_file, chunk, delay):

        data = wav_file.readframes(chunk)

        if self.delay_check:
            if delay >= 1:
                self.clock.sleep(delay)

        if self.module == self.experiment.sounddevice_module_name:
            stream.start()
        elif self.module == self.experiment.pyaudio_module_name:
            stream.start_stream()

        self.set_stimulus_onset()
        start_time = self.clock.time()

        while len(data) > 0:
            # Read data from stdin
            stream.write(data)
            data = wav_file.readframes(chunk)

            if self.duration_check:
                if self.clock.time() - start_time >= self.duration:
                    break

        if self.module == self.experiment.sounddevice_module_name:
            stream.stop()
        elif self.module == self.experiment.pyaudio_module_name:
            stream.stop_stream()

        self.set_stimulus_offset()

        wav_file.close()

        self.show_message(u'Stopped audio')


    def play_data(self, stream, wav_data, chunk, delay):

        if self.delay_check:
            if delay >= 1:
                self.clock.sleep(delay)

        if self.module == self.experiment.sounddevice_module_name:
            stream.start()
        elif self.module == self.experiment.pyaudio_module_name:
            stream.start_stream()

        self.set_stimulus_onset()
        start_time = self.clock.time()

        for start in range(0,len(wav_data),chunk):
            stream.write(wav_data[start:start+chunk])

            if self.duration_check:
                if self.clock.time() - start_time >= self.duration:
                    break

        if self.module == self.experiment.sounddevice_module_name:
            stream.stop()
        elif self.module == self.experiment.pyaudio_module_name:
            stream.stop_stream()

        self.set_stimulus_offset()

        self.show_message(u'Stopped audio')


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


class qtaudio_low_latency_play(audio_low_latency_play, qtautoplugin):

    def __init__(self, name, experiment, script=None):

        """plug-in GUI"""

        audio_low_latency_play.__init__(self, name, experiment, script)
        qtautoplugin.__init__(self, __file__)

