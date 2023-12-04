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
import numpy
import os
import re
import os.path

POLL_TIME = 10
TIMESTAMP = 0

class AudioLowLatencyRecord(Item):

    def reset(self):
        self.var.filename = ''
        self.var.file_exists_action = 'yes'
        self.var.duration = 'infinite'
        self.var.delay_start = 0
        self.var.delay_stop = 0
        self.var.pause_resume = ''
        self.var.stop = ''
        self.var.ram_cache = 'no'

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

        error_msg = 'Duration must be a string named infinite or a an integer greater than 1'
        if isinstance(self.var.duration, str):
            if self.var.duration == 'infinite':
                if self.stop == '':
                    raise OSException(
                        'If duration is set to infinite then setting a stop key is mandatory')
                self.duration_check = False
                self.duration = self.var.duration
            else:
                raise OSException(error_msg)
        elif isinstance(self.var.duration, int):
            if self.var.duration >= 1:
                self.duration_check = True
                self.duration = int(self.var.duration)
                if self.duration < self.period_time:
                    raise OSException(
                        'Duration should be larger than period duration')
            else:
                raise OSException(error_msg)
        else:
            raise OSException(error_msg)

        if isinstance(self.var.delay_start, int):
            if self.var.delay_start >= 0:
                self.delay_start = int(self.var.delay_start)
                if self.delay_start > 0:
                    self.delay_start_check = True
                else:
                    self.delay_start_check = False
            else:
                raise OSException('Start delay can not be negative')
        else:
            raise OSException('Start delay should be a integer')

        if isinstance(self.var.delay_stop, int):
            if self.var.delay_stop >= 0:
                self.delay_stop = int(self.var.delay_stop)
            else:
                raise OSException('Stop delay can not be negative')
        else:
            raise OSException('Stop delay should be a integer')

        if self.dummy_mode == 'no':
            try:
                self._show_message('\n')
                self._show_message('Creating wave file: '+self.filename+' ...')
                self.wav_file = wave.open(self.filename, 'wb')
                self._show_message('Succesfully created wave file...')
            except Exception as e:
                raise OSException(
                    'Could not create wave file\n\nMessage: %s' % e)

            self.wav_file.setsampwidth(self.samplewidth)
            self.wav_file.setframerate(self.samplerate)
            self.wav_file.setnchannels(self.channels)

            self._show_message('Period size: %d frames' % (self.period_size))
            self._show_message('Period size: %d bytes' % (self.data_size))
            self._show_message('Period time: %s ms' % (str(self.period_time)))
            if self.experiment.audio_low_latency_record_module == self.experiment.pyalsaaudio_module_name:
                self._show_message('Buffer consists: %d periods' % (self.periods))
            self._show_message('')

    def run(self):
        start_time = self.set_item_onset()

        if self.dummy_mode == 'no':

            while self.experiment.audio_low_latency_record_locked:
                self.clock.sleep(POLL_TIME)

            if self.delay_start_check:
                self._show_message('Requested audio recording delay: %d ms' % (self.delay_start))
                time_passed = self.clock.time() - start_time
                self._show_message('Time passed: %d ms' % (time_passed))
                delay_start = self.delay_start - time_passed
            else:
                delay_start = self.delay_start

            delay_stop = self.delay_stop

            if self.pause_resume != '' or self.stop != '':
                _keylist = list()
                if self.pause_resume != '':
                    _keylist.extend(self._allowed_responses_pause_resume)
                if self.stop != '':
                    _keylist.extend(self._allowed_responses_stop)
                self.kb.keylist = _keylist
                self.kb.flush()

            self._show_message('Initializing audio recording')
            self._record(self.device, self.wav_file, self.period_size, delay_start, delay_stop)

        elif self.dummy_mode == 'yes':
            self._set_stimulus_onset()
            self._show_message('Dummy mode enabled, NOT recording audio')
        else:
            raise OSException('Error with dummy mode!')

    def _record(self, stream, wav_file, chunk, delay_start, delay_stop):
        frames = list()
        if self.delay_start_check:
            if delay_start >= 1:
                self._show_message('Delaying audio recording for %d ms' % (delay_start))
                self.clock.sleep(delay_start)
                self._show_message('Delay done')
        start_time = self._set_stimulus_onset()
        self._show_message('Starting audio recording')

        if TIMESTAMP == 1:
            timestamp_list = []
            timestamp_list.append(str(self.clock.time()))
        elif TIMESTAMP == 2:
            self._show_message(self.clock.time())

        while True:
            if self.pause_resume != '' or self.stop != '':
                self._check_keys()
            if self.record_execute_pause == 1 and self.record_continue == 1:
                if self.experiment.audio_low_latency_record_module == self.experiment.pyalsaaudio_module_name:
                    stream.pause(True)
                while self.record_execute_pause == 1 and self.record_continue == 1:
                    if self.pause_resume != '' or self.stop != '':
                        self._check_keys()
                if self.experiment.audio_low_latency_record_module == self.experiment.pyalsaaudio_module_name:
                    stream.pause(False)
            if self.duration_check:
                if self.clock.time() - start_time >= self.duration:
                    self._show_message('Audio recording stopping, duration exceeded')
                    self.record_continue = 0
            if self.record_continue == 0:
                if delay_stop >= 1:
                    stop_time = self.clock.time()
                    self._show_message('Initializing stopping audio recording with delay for %d ms' % (delay_stop))
                    while self.clock.time() - stop_time <= delay_stop:
                        self._process_data(stream, wav_file, chunk, frames)
                    self._show_message('Delay done')
                if self.experiment.audio_low_latency_record_module == self.experiment.pyalsaaudio_module_name:
                    stream.drop()
                    self._show_message('ALSA stream stopped')
                break
            self._process_data(stream, wav_file, chunk, frames)

            if TIMESTAMP == 1:
                timestamp_list.append(str(self.clock.time()))
            elif TIMESTAMP == 2:
                self._show_message(self.clock.time())

        self._set_stimulus_offset()

        self._show_message('Processing audio data done!')
        time_elapsed_processing = int(round(self.clock.time() - start_time))
        self._show_message('Elapsed time: %d ms' % time_elapsed_processing)

        if self.ram_cache == 'yes':
            self._show_message('Writing data to wav file')
            wav_file.writeframes(b''.join(frames))
        wav_file.close()
        self._show_message('Finished audio recording')
        self.wav_duration = round((self.clock.time() - start_time) / 1000, 1)
        self._show_message('Duration recorded wave file: %d s' % self.wav_duration)
        self.experiment.audio_low_latency_record_locked = 0

    def _init_var(self):
        self.dummy_mode = self.experiment.audio_low_latency_record_dummy_mode
        self.verbose = self.experiment.audio_low_latency_record_verbose
        if self.dummy_mode == 'no':
            self.module = self.experiment.audio_low_latency_record_module
            self.device = self.experiment.audio_low_latency_record_device
            if self.experiment.audio_low_latency_record_module == self.experiment.pyalsaaudio_module_name:
                self.buffer_size = self.experiment.audio_low_latency_record_buffer_size
                self.periods = self.experiment.audio_low_latency_record_periods
        self.period_size = self.experiment.audio_low_latency_record_period_size
        self.period_time = self.experiment.audio_low_latency_record_period_time
        self.data_size = self.experiment.audio_low_latency_record_data_size
        self.bitdepth = self.experiment.audio_low_latency_record_bitdepth
        self.samplewidth = self.experiment.audio_low_latency_record_samplewidth
        self.samplerate = self.experiment.audio_low_latency_record_samplerate
        self.channels = self.experiment.audio_low_latency_record_channels

        self.file_exists_action = self.var.file_exists_action
        self.filename = self._build_output_file()
        self.pause_resume = self.var.pause_resume
        self.stop = self.var.stop
        self.ram_cache = self.var.ram_cache
        self.record_continue = 1
        self.record_execute_pause = 0

    def _check_init(self):
        if not hasattr(self.experiment, 'audio_low_latency_record_device'):
            raise OSException(
                'Audio Low Latency Record Init item is missing')

    def _generate_suffix(self, path_to_file):
        pattern = "_[0-9]+$"
        (filename, ext) = os.path.splitext(path_to_file)

        # Keep increasing suffix number if file with the current suffix already exists
        filename_exists = True
        while filename_exists:
            match = re.search(pattern, filename)
            if match:
                no = int(filename[match.start() + 1:]) + 1
                filename = re.sub(pattern, "_" + str(no), filename)
            else:
                filename = filename + "_1"

            new_filename = filename + ext
            if not os.path.exists(new_filename):
                filename_exists = False

        return new_filename

    def _build_output_file(self):
        extension = '.wav'
        # Make output location relative to location of experiment
        rel_loc = os.path.normpath(self.var.filename)
        if self.var.logfile is None:
            raise OSException("Path to log file not found.")
        output_file = os.path.normpath(os.path.join(os.path.dirname(self.var.logfile), rel_loc)) + extension
        # Check for a subfolder (when it is specified) that it exists and if not, create it
        if os.path.exists(os.path.dirname(output_file)):
            if self.file_exists_action == 'yes':
                # Search for underscore/number suffixes
                output_file = self._generate_suffix(output_file)
        else:
            if os.path.dirname(rel_loc) != "":
                try:
                    os.makedirs(os.path.dirname(output_file))
                except Exception as e:
                    raise OSException("Error creating sound file: " + str(e))
        return output_file

    def _process_data(self, stream, wav_file, chunk, frames):
        # Read data from device
        if self.module == self.experiment.pyalsaaudio_module_name:
            l, data = stream.read()
        else:
            data = stream.read(chunk)
            if self.module == self.experiment.sounddevice_module_name:
                data = numpy.frombuffer(data[0])

        # save data to file/ram
        if self.ram_cache == 'yes':
            frames.append(data)
        elif self.ram_cache == 'no':
            wav_file.writeframes(data)

    def _check_keys(self):
        key1, time1 = self.kb.get_key()
        self.kb.flush()
        if self.stop != '':
            if key1 in self._allowed_responses_stop:
                self._show_message('Detected key press for stopping audio')
                self.record_continue = 0
        if self.pause_resume != '':
            if key1 in self._allowed_responses_pause_resume:
                if self.record_execute_pause == 0:
                    self._show_message('Detected key press for pausing audio recording')
                    self.record_execute_pause = 1
                elif self.record_execute_pause == 1:
                    self._show_message('Detected key press for resuming audio recording')
                    self.record_execute_pause = 0

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


class QtAudioLowLatencyRecord(AudioLowLatencyRecord, QtAutoPlugin):

    def __init__(self, name, experiment, script=None):
        AudioLowLatencyRecord.__init__(self, name, experiment, script)
        QtAutoPlugin.__init__(self, __file__)
