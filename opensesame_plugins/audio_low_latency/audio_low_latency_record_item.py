"""
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

__author__ = "Bob Rosbag"
__license__ = "GPLv3"

import os
import wave

from libopensesame.exceptions import OSException
from libopensesame.oslogging import oslogger

from .audio_low_latency_item import (AudioLowLatencyStreamItem, PYALSAAUDIO,
                                     SOUNDDEVICE, TIMESTAMP)


class AudioLowLatencyRecordItem(AudioLowLatencyStreamItem):
    """Base class of the record (foreground) and record start (background)
    items.
    """

    kind = 'record'
    lock_poll_time = 10

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
        self.file_exists_action = self.var.file_exists_action
        if self.file_exists_action not in ('yes', 'no'):
            raise OSException(f'Do not overwrite existing files should be yes or no, not {self.file_exists_action}')
        self.filename = self._build_output_file()
        self._check_ram_cache('Cache to RAM')
        self._init_keys()

        if self.var.duration == 'infinite':
            # The background item can be stopped by a stop item
            if not self.background and not self._allowed_responses_stop:
                raise OSException(
                    'If duration is set to infinite then setting a stop key is mandatory')
            self.duration_check = False
            self.duration = self.var.duration
        elif isinstance(self.var.duration, int) and self.var.duration >= 1:
            self.duration_check = True
            self.duration = self.var.duration
            if self.duration < self.period_time:
                raise OSException(
                    'Duration should be larger than period duration')
        else:
            raise OSException(
                f'Duration should be infinite or a positive integer (ms), not {self.var.duration}')

        self.delay_start = self._check_delay('delay_start', 'Start delay')
        self.delay_start_check = self.delay_start > 0
        self.delay_stop = self._check_delay('delay_stop', 'Stop delay')

        if self.dummy_mode == 'no':
            try:
                self._show_message('\n')
                self._show_message(f"Creating wave file: {self.filename} ...")
                self.wav_file = wave.open(self.filename, 'wb')
                self._show_message('Successfully created wave file...')
            except Exception as e:
                raise OSException(f"Could not create wave file\n\nMessage: {e}")

            self.wav_file.setsampwidth(self.samplewidth)
            self.wav_file.setframerate(self.samplerate)
            self.wav_file.setnchannels(self.channels)

            self._show_message(f"Period size: {self.period_size} frames")
            self._show_message(f"Period size: {self.data_size} bytes")
            self._show_message(f"Period time: {self.period_time} ms")
            if self.module == PYALSAAUDIO:
                self._show_message(f"Buffer consists: {self.periods} periods")
            self._show_message('')
        else:
            self._show_message('Dummy mode enabled, prepare phase')

    def run(self):
        if self.background:
            self._check_stop_wait()
            # The pause and resume items check the keys of the start item
            # that ran last, not of the one that was prepared last
            self._set('pause_resume_key', self.pause_resume)
            # Only a stop item can end it: the wait item checks this
            self._set('infinite', int(not self.duration_check and not self._allowed_responses_stop))
        self.set_item_onset()
        _start_time = self.clock.time()

        if self.dummy_mode == 'no':
            self._wait_until_unlocked()

            if self.delay_start_check:
                self._show_message(f"Requested audio recording delay: {self.delay_start} ms")
                time_passed = self.clock.time() - _start_time
                self._show_message(f"Time passed: {time_passed} ms")
                delay_start = round(self.delay_start - time_passed, 1)
            else:
                delay_start = self.delay_start

            self._start_keys()
            self._show_message('Initializing audio recording')
            args = (self.device, self.wav_file, self.period_size, delay_start, self.delay_stop)
            if self.background:
                self._start_thread(self._record, args)
            else:
                self._record(*args)
        else:
            self._set_stimulus_onset()
            self._show_message('Dummy mode enabled, NOT recording audio')

    def _record(self, stream, wav_file, chunk, delay_start, delay_stop):
        pause_duration = 0
        self.overruns = 0
        self.duration_exceeded = False

        frames = []
        if self.delay_start_check:
            if delay_start >= 1:
                self._show_message(f"Delaying audio recording for {delay_start} ms")
                self._sleep(delay_start)
                self._show_message('Delay done')
        self.start_time = self._set_stimulus_onset()
        self._show_message('Starting audio recording')

        if TIMESTAMP == 1:
            timestamp_list = []
            timestamp_list.append(str(self.clock.time()))
        elif TIMESTAMP == 2:
            self._show_message(self.clock.time())

        while True:
            if self._keylist:
                self._check_keys()
            if self._paused():
                pause_duration += self._wait_while_paused(stream)
            if self.duration_check and not self.duration_exceeded:
                self._check_duration()
            if self._flag('continue') == 0 or self.duration_exceeded:
                if delay_stop >= 1:
                    stop_time = self.clock.time()
                    self._show_message(f"Initializing stopping audio recording with delay for {delay_stop} ms")
                    while self.clock.time() - stop_time <= delay_stop:
                        self._process_data(stream, wav_file, chunk, frames)
                    self._show_message('Delay done')
                    self._show_message('Stopped audio recording')
                break

            self._process_data(stream, wav_file, chunk, frames)

            if TIMESTAMP == 1:
                timestamp_list.append(str(self.clock.time()))
            elif TIMESTAMP == 2:
                self._show_message(self.clock.time())

        if self.module == PYALSAAUDIO:
            stream.drop()
            self._show_message('ALSA stream stopped')

        self._set_stimulus_offset()

        self._show_message('Processing audio data done!')
        time_elapsed_processing = int(round(self.clock.time() - self.start_time))
        self._show_message(f"Elapsed time: {time_elapsed_processing} ms")

        if self.ram_cache == 'yes':
            self._show_message('Writing data to wav file')
            wav_file.writeframes(b''.join(frames))
        wav_file_nframes = wav_file.getnframes()
        self.wav_duration = round(float(wav_file_nframes) / float(wav_file.getframerate()) * 1000, 1)

        wav_file.close()
        if self.overruns:
            oslogger.warning(f'{self.overruns} buffer overrun(s) during audio recording: '
                             'parts of the recording are missing')
        self._show_message('Finished audio recording')
        self._show_message(f"Duration recorded wave file: {self.wav_duration} ms")

    def _free_filename(self, path_to_file):
        """Returns path_to_file, or, when that file exists, the first free
        name with _1, _2, ... before the extension.
        """
        if not os.path.exists(path_to_file):
            return path_to_file
        (filename, ext) = os.path.splitext(path_to_file)
        number = 1
        while os.path.exists(f"{filename}_{number}{ext}"):
            number += 1
        return f"{filename}_{number}{ext}"

    def _build_output_file(self):
        extension = '.wav'
        # Make output location relative to location of experiment
        if str(self.var.filename).strip() == '':
            raise OSException('Audio filename is empty')
        rel_loc = os.path.normpath(str(self.var.filename))
        if self.var.logfile is None:
            raise OSException("Path to log file not found.")
        output_file = f"{os.path.normpath(os.path.join(os.path.dirname(self.var.logfile), rel_loc))}{extension}"
        # Check for a subfolder (when it is specified) that it exists and if not, create it
        if os.path.exists(os.path.dirname(output_file)):
            if self.file_exists_action == 'yes':
                output_file = self._free_filename(output_file)
        else:
            if os.path.dirname(rel_loc) != "":
                try:
                    os.makedirs(os.path.dirname(output_file))
                except Exception as e:
                    raise OSException(f"Error creating sound file: {e}")
        return output_file

    def _process_data(self, stream, wav_file, chunk, frames):
        # Read data from device
        if self.module == PYALSAAUDIO:
            l, data = stream.read()
            # A negative length is an overrun: audio data was lost
            if l < 0:
                self.overruns += 1
        elif self.module == SOUNDDEVICE:
            data = bytes(stream.read(chunk)[0])

        # save data to file/ram
        if self.ram_cache == 'yes':
            frames.append(data)
        else:
            wav_file.writeframes(data)
