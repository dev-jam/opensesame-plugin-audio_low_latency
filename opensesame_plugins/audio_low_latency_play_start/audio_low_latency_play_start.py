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
import threading
import wave

VERSION = u'8.6.0'

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
        self.var.pause_resume = u''
        self.var.stop = u''
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
        self.pause_resume = self.var.pause_resume
        self.stop = self.var.stop
        self.ram_cache = self.var.ram_cache

        self.experiment.audio_low_latency_play_continue = 1
        self.experiment.audio_low_latency_play_start = 1
        self.experiment.audio_low_latency_play_execute_pause = 0


    def prepare(self):

        """Preparation phase"""

        # Call the parent constructor.
        item.prepare(self)

        # create keyboard object
        self.kb = keyboard(self.experiment,timeout=1)

        self.init_var()

        if self.pause_resume != u'':
            # Prepare the pause resume responses
            self._allowed_responses_pause_resume = []
            for r in safe_decode(self.pause_resume).split(u';'):
                if r.strip() != u'':
                    self._allowed_responses_pause_resume.append(r)
            if not self._allowed_responses_pause_resume:
                self._allowed_responses_pause_resume = None
            self.show_message(u"allowed pause/resume keys set to %s" % self._allowed_responses_pause_resume)

        if self.stop != u'':
            # Prepare the pause resume responses
            self._allowed_responses_stop = []
            for r in safe_decode(self.stop).split(u';'):
                if r.strip() != u'':
                    self._allowed_responses_stop.append(r)
            if not self._allowed_responses_stop:
                self._allowed_responses_stop = None
            self.show_message(u"allowed stop keys set to %s" % self._allowed_responses_stop)

        error_msg = u'Duration must be a string named sound or a an integer greater than 1'

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

        if isinstance(self.var.duration,str):
            if self.var.duration == u'sound':
                self.duration_check = False
                self.duration = self.wav_duration
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


    def run(self):

        """Run phase"""

        if not (hasattr(self.experiment, "audio_low_latency_play_stop") or hasattr(self.experiment, "audio_low_latency_play_wait")):
            raise osexception(
                    u'Audio Low Latency Play Stop or Audio Low Latency Play Wait item is missing')

        start_time = self.set_item_onset()

        if self.dummy_mode == u'no':

            while self.experiment.audio_low_latency_play_locked:
                self.clock.sleep(self.poll_time)

            if self.delay_check:
                time_passed = self.clock.time() - start_time
                delay = self.delay - time_passed
            else:
                delay = self.delay

            if self.pause_resume != u'' or self.stop != u'':
                _keylist = list()
                if self.pause_resume != u'':
                    _keylist.extend(self._allowed_responses_pause_resume)
                if self.stop != u'':
                    _keylist.extend(self._allowed_responses_stop)

                self.kb.keylist = _keylist
                self.kb.flush()

            self.show_message(u'Initializing audio playback')

            self.experiment.audio_low_latency_play_locked = 1

            if self.ram_cache == u'no':
                self.experiment.audio_low_latency_play_thread = threading.Thread(target=self.play, args=(self.device, self.wav_file, self.period_size, delay))
            elif self.ram_cache == u'yes':
                self.experiment.audio_low_latency_play_thread = threading.Thread(target=self.play, args=(self.device, self.wav_file, self.data_size, delay, self.wav_file_data))

            self.experiment.audio_low_latency_play_thread.start()

        elif self.dummy_mode == u'yes':
            self.set_stimulus_onset()
            self.show_message(u'Dummy mode enabled, NOT playing audio')
        else:
            raise osexception(u'Error with dummy mode!')


    def play(self, stream, wav_file, chunk, delay, wav_data=None):

        self.experiment.audio_low_latency_play_thread_running = 1

        start = 0

        if self.ram_cache == u'no':
            # Read data from wave
            data = wav_file.readframes(chunk)
        elif self.ram_cache == u'yes':
            data = wav_data[start:start+chunk]

        self.show_message(u'Chunk size: %d bytes' % (len(data)))

        if self.delay_check:
            if delay >= 1:
                self.show_message(u'Delaying audio playback for %d ms' % (delay))
                self.clock.sleep(delay)
                self.show_message(u'Delay done')

        start_time = self.set_stimulus_onset()

        self.show_message(u'Starting audio playback')

        while len(data) > 0:

            # write data to device
            stream.write(data)

            if self.ram_cache == u'no':
                # Read data from wave
                data = wav_file.readframes(chunk)
            elif self.ram_cache == u'yes':
                if len(wav_data) >= start+chunk:
                    data = wav_data[start:start+chunk]
                elif len(wav_data) < start+chunk:
                    data = wav_data[start:len(wav_data)]

                start += chunk

            # check for stop/pause/resume key
            if self.pause_resume != u'' or self.stop != u'':
                self.check_keys()

            while self.experiment.audio_low_latency_play_execute_pause == 1 and self.experiment.audio_low_latency_play_continue == 1:
                if self.pause_resume != u'' or self.stop != u'':
                    self.check_keys()

            if self.experiment.audio_low_latency_play_continue == 0:
                break
            elif self.duration_check:
                if self.clock.time() - start_time >= self.duration:
                    self.show_message(u'Audio playback stopped, duration exceeded')
                    break

        self.set_stimulus_offset()

        if self.ram_cache == u'no':
            wav_file.close()

        self.show_message(u'Finished audio playback')
        self.experiment.audio_low_latency_play_locked = 0


    def check_keys(self):
        """
        desc:
            Show message.
        """

        key1, time1 = self.kb.get_key()
        self.kb.flush()
        if self.stop != u'':
            if key1 in self._allowed_responses_stop:
                self.show_message(u'Stopped audio playback')
                self.experiment.audio_low_latency_play_continue = 0
        if self.pause_resume != u'':
            if key1 in self._allowed_responses_pause_resume:
                if self.experiment.audio_low_latency_play_execute_pause == 0:
                    self.show_message(u'Paused audio playback')
                    self.experiment.audio_low_latency_play_execute_pause = 1
                elif self.experiment.audio_low_latency_play_execute_pause == 1:
                    self.show_message(u'Resumed audio playback')
                    self.experiment.audio_low_latency_play_execute_pause = 0

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


class qtaudio_low_latency_play_start(audio_low_latency_play_start, qtautoplugin):

    def __init__(self, name, experiment, script=None):

        """plug-in GUI"""

        audio_low_latency_play_start.__init__(self, name, experiment, script)
        qtautoplugin.__init__(self, __file__)

