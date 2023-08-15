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

from libopensesame.py3compat import *
from libopensesame.item import Item
from libqtopensesame.items.qtautoplugin import QtAutoPlugin
from libopensesame.exceptions import OSException
from libopensesame.oslogging import oslogger
from openexp.keyboard import Keyboard
import wave

POLL_TIME = 1


class AudioLowLatencyPlay(Item):

    def reset(self):
        self.var.filename = ''
        self.var.duration = 'sound'
        self.var.delay = 0
        self.var.pause_resume = ''
        self.var.stop = ''
        self.var.ram_cache = 'yes'

    def prepare(self):
        super().prepare()
        self._check_init()
        self._init_var()
        self.kb = Keyboard(self.experiment, timeout=1)

        if self.pause_resume != '':
            self._allowed_responses_pause_resume = []
            for r in safe_decode(self.pause_resume).split(';'):
                if r.strip() != '':
                    self._allowed_responses_pause_resume.append(r)
            if not self._allowed_responses_pause_resume:
                self._allowed_responses_pause_resume = None
            self._show_message("allowed pause/resume keys set to %s" % self._allowed_responses_pause_resume)

        if self.stop != '':
            self._allowed_responses_stop = []
            for r in safe_decode(self.stop).split(';'):
                if r.strip() != '':
                    self._allowed_responses_stop.append(r)
            if not self._allowed_responses_stop:
                self._allowed_responses_stop = None
            self._show_message("allowed stop keys set to %s" % self._allowed_responses_stop)

        error_msg = 'Duration must be a string named sound or a an integer greater than 1'

        try:
            self._show_message('\n')
            self._show_message('Loading sound file: '+self.filename+' ...')
            self.wav_file = wave.open(self.filename, 'rb')
            self._show_message('Succesfully loaded sound file...')
        except Exception as e:
            raise OSException(
                'Could not load audio file\n\nMessage: %s' % e)

        self.wav_duration = int(round(float(self.wav_file.getnframes()) / float(self.wav_file.getframerate()) * 1000, 1))
        self._show_message('Audio file duration: %d ms' % (self.wav_duration))
        self._show_message('Period size: %d frames' % (self.period_size))
        self._show_message('Period duration: %s ms' % (str(self.period_size_time)))

        error_msg_list = []

        if self.wav_file.getsampwidth() * 8 != self.bitdepth:
            error_msg_list.append('- bitdepth incorrect, file is %dbit but experiment is set to %dbit\n' % (self.wav_file.getsampwidth()*8, self.bitdepth))
        if self.wav_file.getframerate() != self.samplerate:
            error_msg_list.append('- samplerate incorrect, file is %dHz but experiment is set to %dHz\n' % (self.wav_file.getframerate(), self.samplerate))
        if self.wav_file.getnchannels() != self.channels:
            error_msg_list.append('- number of channels incorrect, file has %d channel(s) but experiment is set to %d channel(s)\n' % (self.wav_file.getnchannels(), self.channels))
        if self.wav_file.getnframes() < self.period_size:
            error_msg_list.append('- Period size is larger than total number of frames in wave file, use a period size smaller than %d frames\n' % (self.wav_file.getnframes()))
        if error_msg_list:
            raise OSException('Error with audio file %s\n%s' % (self.filename, ''.join(error_msg_list)))

        if self.ram_cache == 'yes':
            wav_file_nframes = self.wav_file.getnframes()
            self._show_message('Loading wave file into cache...')
            self.wav_file_data = self.wav_file.readframes(wav_file_nframes)
            self._show_message('Done! Closing wave file...')
            self.wav_file.close()
        elif self.ram_cache == 'no':
            self._show_message('Reading directly from wave file, no cache')

        if isinstance(self.var.duration, str):
            if self.var.duration == 'sound':
                self.duration_check = False
                self.duration = self.wav_duration
            else:
                raise OSException(error_msg)
        elif isinstance(self.var.duration, int):
            if self.var.duration >= 1:
                self.duration_check = True
                self.duration = int(self.var.duration)
            else:
                raise OSException(error_msg)
        else:
            raise OSException(error_msg)

        if isinstance(self.var.delay, int):
            if self.var.delay >= 0:
                self.delay = int(self.var.delay)
                if self.delay > 0:
                    self.delay_check = True
                else:
                    self.delay_check = False
            else:
                raise OSException('Delay can not be negative')
        else:
            raise OSException('Delay should be a integer')

    def run(self):
        start_time = self.set_item_onset()

        if self.dummy_mode == 'no':
            while self.experiment.audio_low_latency_play_locked:
                self.clock.sleep(POLL_TIME)
            if self.delay_check:
                time_passed = self.clock.time() - start_time
                delay = self.delay - time_passed
            else:
                delay = self.delay
            if self.pause_resume != '' or self.stop != '':
                _keylist = list()
                if self.pause_resume != '':
                    _keylist.extend(self._allowed_responses_pause_resume)
                if self.stop != '':
                    _keylist.extend(self._allowed_responses_stop)
                self.kb.keylist = _keylist
                self.kb.flush()
            self._show_message('Initializing audio playback')
            if self.ram_cache == 'no':
                self._play(self.device, self.wav_file, self.period_size, delay)
            elif self.ram_cache == 'yes':
                self._play(self.device, self.wav_file, self.data_size, delay, self.wav_file_data)
        elif self.dummy_mode == 'yes':
            self._set_stimulus_onset()
            self._show_message('Dummy mode enabled, NOT playing audio')
        else:
            raise OSException('Error with dummy mode!')

    def _play(self, stream, wav_file, chunk, delay, wav_data=None):
        start = 0
        if self.ram_cache == 'no':
            # Read data from wave
            data = wav_file.readframes(chunk)
        elif self.ram_cache == 'yes':
            data = wav_data[start:start+chunk]
        self._show_message('Chunk size: %d bytes' % (self.experiment.audio_low_latency_play_data_size))
        if self.delay_check:
            if delay >= 1:
                self._show_message('Delaying audio playback for %d ms' % (delay))
                self.clock.sleep(delay)
                self._show_message('Delay done')
        start_time = self._set_stimulus_onset()
        self._show_message('Starting audio playback')

        while len(data) == self.experiment.audio_low_latency_play_data_size:
            stream.write(data)
            if self.ram_cache == 'no':
                # Read data from wave
                data = wav_file.readframes(chunk)
            elif self.ram_cache == 'yes':
                if len(wav_data) >= start+chunk:
                    data = wav_data[start:start+chunk]
                elif len(wav_data) < start+chunk:
                    data = wav_data[start:len(wav_data)]
                start += chunk
            if self.pause_resume != '' or self.stop != '':
                self._check_keys()
            while self.play_execute_pause == 1 and self.play_continue == 1:
                if self.pause_resume != '' or self.stop != '':
                    self._check_keys()
            if self.play_continue == 0:
                break
            elif self.duration_check:
                if self.clock.time() - start_time >= self.duration:
                    self._show_message('Audio playback stopped, duration exceeded')
                    break
        self._set_stimulus_offset()
        if self.ram_cache == 'no':
            wav_file.close()
        self._show_message('Finished audio playback')

    def _check_keys(self):
        key1, time1 = self.kb.get_key()
        self.kb.flush()
        if self.stop != '':
            if key1 in self._allowed_responses_stop:
                self._show_message('Stopped audio playback')
                self.play_continue = 0
        if self.pause_resume != '':
            if key1 in self._allowed_responses_pause_resume:
                if self.play_execute_pause == 0:
                    self._show_message('Paused audio playback')
                    self.play_execute_pause = 1
                elif self.play_execute_pause == 1:
                    self._show_message('Resumed audio playback')
                    self.play_execute_pause = 0

    def _init_var(self):
        self.dummy_mode = self.experiment.audio_low_latency_play_dummy_mode
        self.verbose = self.experiment.audio_low_latency_play_verbose
        if self.dummy_mode == 'no':
            self.module = self.experiment.audio_low_latency_play_module
            self.device = self.experiment.audio_low_latency_play_device
        self.period_size = self.experiment.audio_low_latency_play_period_size
        self.period_size_time = self.experiment.audio_low_latency_play_period_size_time
        self.data_size = self.experiment.audio_low_latency_play_data_size
        self.bitdepth = self.experiment.audio_low_latency_play_bitdepth
        self.samplewidth = self.experiment.audio_low_latency_play_samplewidth
        self.samplerate = self.experiment.audio_low_latency_play_samplerate
        self.channels = self.experiment.audio_low_latency_play_channels

        self.filename = self.experiment.pool[self.var.filename]
        self.pause_resume = self.var.pause_resume
        self.stop = self.var.stop
        self.ram_cache = self.var.ram_cache
        self.play_continue = 1
        self.play_execute_pause = 0

    def _check_init(self):
        if not hasattr(self.experiment, 'audio_low_latency_play_device'):
            raise OSException(
                'Audio Low Latency Play Init item is missing')

    def _show_message(self, message):
        oslogger.debug(message)
        if self.verbose == 'yes':
            print(message)

    def _set_stimulus_onset(self, time=None):
        if time is None:
            time = self.clock.time()
        self.experiment.var.set('time_stimulus_onset_%s' % self.name, time)
        return time

    def _set_stimulus_offset(self, time=None):
        if time is None:
            time = self.clock.time()
        self.experiment.var.set('time_stimulus_offset_%s' % self.name, time)
        return time

    def _set_stimulus_timing(self, _type, time=None):
        if time is None:
            time = self.clock.time()
        self.experiment.var.set('time_stimulus_%s_%s' % (_type, self.name), time)
        return time


class QtAudioLowLatencyPlay(AudioLowLatencyPlay, QtAutoPlugin):

    def __init__(self, name, experiment, script=None):
        AudioLowLatencyPlay.__init__(self, name, experiment, script)
        QtAutoPlugin.__init__(self, __file__)
