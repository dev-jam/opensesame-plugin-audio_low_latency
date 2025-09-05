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

from libopensesame.py3compat import *
from libopensesame.item import Item
from libqtopensesame.items.qtautoplugin import QtAutoPlugin
from libopensesame.exceptions import OSException
from libopensesame.oslogging import oslogger
from openexp.keyboard import Keyboard
import wave

POLL_TIME = 1
TIMESTAMP = 0

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
            self._show_message(f"allowed pause/resume keys set to {self._allowed_responses_pause_resume}")

        if self.stop != '':
            self._allowed_responses_stop = []
            for r in safe_decode(self.stop).split(';'):
                if r.strip() != '':
                    self._allowed_responses_stop.append(r)
            if not self._allowed_responses_stop:
                self._allowed_responses_stop = None
            self._show_message(f"allowed stop keys set to {self._allowed_responses_stop}")

        if isinstance(self.var.delay, int):
            if self.var.delay >= 0:
                self.delay = int(self.var.delay)
                self.delay_check = self.delay > 0
            else:
                raise OSException('Delay can not be negative')
        else:
            raise OSException('Delay should be a integer')

        if self.dummy_mode == 'no':
            try:
                self._show_message('\n')
                self._show_message(f"Loading sound file: {self.filename} ...")
                self.wav_file = wave.open(self.filename, 'rb')
                self._show_message('Succesfully loaded sound file...')
            except Exception as e:
                raise OSException(f"Could not load audio file\n\nMessage: {e}")

            error_msg_list = []

            if self.wav_file.getsampwidth() * 8 != self.bitdepth:
                error_msg_list.append(f"- bitdepth incorrect, file is {self.wav_file.getsampwidth()*8}bit but experiment is set to {self.bitdepth}bit\n")
            if self.wav_file.getframerate() != self.samplerate:
                error_msg_list.append(f"- samplerate incorrect, file is {self.wav_file.getframerate()}Hz but experiment is set to {self.samplerate}Hz\n")
            if self.wav_file.getnchannels() != self.channels:
                error_msg_list.append(f"- number of channels incorrect, file has {self.wav_file.getnchannels()} channel(s) but experiment is set to {self.channels} channel(s)\n")
            if self.wav_file.getnframes() < self.period_size:
                error_msg_list.append(f"- Period size is larger than total number of frames in wave file, use a period size smaller than {self.wav_file.getnframes()} frames\n")
            if error_msg_list:
                raise OSException(f"Error with audio file {self.filename}\n{''.join(error_msg_list)}")

            wav_file_nframes = self.wav_file.getnframes()
            self.wav_duration = round(float(wav_file_nframes) / float(self.wav_file.getframerate()) * 1000, 1)
            n_periods = round(wav_file_nframes / self.period_size, 2)
            self.experiment.var.wav_duration = self.wav_duration
            self._show_message(f"Audio file duration: {self.wav_duration} ms")
            self._show_message(f"Wave file contains: {wav_file_nframes} frames")
            self._show_message(f"Period size: {self.period_size} frames")
            self._show_message(f"Period size: {self.data_size} bytes")
            self._show_message(f"Period time: {self.period_time} ms")
            self._show_message(f"Number of periods to be played: {n_periods} periods")
            if self.experiment.audio_low_latency_play_module == self.experiment.pyalsaaudio_module_name:
                n_buffers = round(n_periods / self.periods, 2)
                self._show_message(f"Buffer consists: {self.periods} periods")
                self._show_message(f"Number of buffers to be played: {n_buffers} buffers")
            self._show_message('')

            error_msg = 'Duration must be a string named sound or a an integer greater than 1'
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

            if self.ram_cache == 'yes':
                self._show_message('Loading wave file into cache...')
                self.wav_file_data = self.wav_file.readframes(wav_file_nframes)
                self._show_message('Done! Closing wave file...')
                self.wav_file.close()
            elif self.ram_cache == 'no':
                self._show_message('Reading directly from wave file, no cache')

        elif self.dummy_mode == 'yes':
            self._set_stimulus_onset()
            self._show_message('Dummy mode enabled, prepare phase')
        else:
            raise OSException('Error with dummy mode!')


    def run(self):
        self.set_item_onset()
        _start_time = self.clock.time()

        if self.dummy_mode == 'no':
            while self.experiment.audio_low_latency_play_locked:
                self.clock.sleep(POLL_TIME)
            if self.delay_check:
                time_passed = self.clock.time() - _start_time
                delay = self.delay - time_passed
            else:
                delay = self.delay
            if self.pause_resume != '' or self.stop != '':
                _keylist = []
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

        period = 0
        pause_duration = 0

        self.duration_exceeded = False

        if self.ram_cache == 'no':
            data = wav_file.readframes(chunk)
        elif self.ram_cache == 'yes':
            start = 0
            data = wav_data[start:start+chunk]
            start += chunk
        data_length = len(data)
        self._show_message(f"Chunk size: {data_length} bytes")
        if self.delay_check:
            if delay >= 1:
                self._show_message(f"Delaying audio playback for {delay} ms")
                self.clock.sleep(delay)
                self._show_message('Delay done')
        self.start_time = self._set_stimulus_onset()
        self._show_message('Starting audio playback')

        if TIMESTAMP == 1:
            timestamp_list = []
            timestamp_list.append(str(self.clock.time()))
        elif TIMESTAMP == 2:
            self._show_message(self.clock.time())

        while len(data) > 0:

            stream.write(data)
            period += 1

            if TIMESTAMP == 1:
                timestamp_list.append(str(self.clock.time()))
            elif TIMESTAMP == 2:
                self._show_message(self.clock.time())

            if self.ram_cache == 'no':
                data = wav_file.readframes(chunk)
                data_length = len(data)
            elif self.ram_cache == 'yes':
                if start+chunk <= len(wav_data):
                    data = wav_data[start:start+chunk]
                    data_length = len(data)
                elif start+chunk > len(wav_data) and start < len(wav_data):
                    data = wav_data[start:start+len(wav_data)]
                    data_length = len(data)
                elif start+chunk > len(wav_data) and start >= len(wav_data):
                    data = []
                start += chunk

            if self.pause_resume != '' or self.stop != '':
                self._check_keys()
            if self.play_execute_pause == 1 and self.play_continue == 1:
                self._show_message('Paused audio playback')
                pause_start_time = self.clock.time()
                if self.experiment.audio_low_latency_play_module == self.experiment.pyalsaaudio_module_name:
                    stream.pause(True)
                while self.play_execute_pause == 1 and self.play_continue == 1:
                    if self.pause_resume != '' or self.stop != '':
                        self._check_keys()
                    if self.duration_check:
                        if self._check_duration():
                            break
                if self.experiment.audio_low_latency_play_module == self.experiment.pyalsaaudio_module_name:
                    stream.pause(False)
                self._show_message('Resumed audio playback')
                pause_stop_time = self.clock.time()
                pause_duration += pause_stop_time - pause_start_time
            if self.duration_check and not self.duration_exceeded:
                self._check_duration()
            if self.play_continue == 0 or self.duration_exceeded:
                self._show_message('Stopped audio playback')
                break

        if self.experiment.audio_low_latency_play_module == self.experiment.pyalsaaudio_module_name:
            stream.drop()
            self._show_message('ALSA stream stopped')

        self._show_message('Processing audio data done!')

        playback_duration = int(round(period * self.period_time_exact))
        time_elapsed_processing = int(round(self.clock.time() - self.start_time))
        time_elapsed_processing_real = time_elapsed_processing - pause_duration
        self._show_message(f"Elapsed time: {time_elapsed_processing} ms")

        self._show_message(f"Processed wave playback duration: {playback_duration} ms")
        self._show_message(f"Current wave playback duration: {time_elapsed_processing_real} ms")
        self.experiment.var.wait_to_finish = int(round(playback_duration - time_elapsed_processing_real))
        if self.experiment.var.wait_to_finish > 0:
            self._show_message(f"Waiting {self.experiment.var.wait_to_finish} ms for audio to finish")
            self.clock.sleep(self.experiment.var.wait_to_finish)

        self._set_stimulus_offset()
        if self.ram_cache == 'no':
            wav_file.close()
        self._show_message('Finished audio playback')
        self._show_message('')

        if self.experiment.audio_low_latency_play_module == self.experiment.pyalsaaudio_module_name:
            mod_period = (period - 1) % self.periods + 1
            self._show_message(f"Number of periods played: {period}")
            self._show_message(f"Finished in period: {mod_period}")
            #self.experiment.var.mod_period = mod_period
            #self.experiment.var.data_length = data_length
            #self._show_message(f"Full period length: {self.data_size} bytes")
            #self._show_message(f"Last period length: {data_length} bytes")

        if TIMESTAMP == 1:
            self._show_message("\n".join(timestamp_list))

    def _check_keys(self):
        key1, time1 = self.kb.get_key()
        self.kb.flush()
        if self.stop != '':
            if key1 in self._allowed_responses_stop:
                self._show_message('Detected key press for stopping audio')
                self._log_keys(key1, str(time1))
                self.play_continue = 0
        if self.pause_resume != '':
            if key1 in self._allowed_responses_pause_resume:
                self._log_keys(key1, str(time1))
                if self.play_execute_pause == 0:
                    self._show_message('Detected key press for pausing audio playback')
                    self.play_execute_pause = 1
                elif self.play_execute_pause == 1:
                    self._show_message('Detected key press for resuming audio playback')
                    self.play_execute_pause = 0

    def _log_keys(self, key1, time1):
        self.experiment.var.audio_low_latency_play_key_presses += f"{key1};"
        self.experiment.var.audio_low_latency_play_key_timestamps += f"{time1};"

    def _check_duration(self):
        if self.clock.time() - self.start_time >= self.duration:
            self._show_message('Stopping audio playback, duration exceeded')
            self.duration_exceeded = True
            return True
        else:
            return False

    def _init_var(self):
        self.dummy_mode = self.experiment.audio_low_latency_play_dummy_mode
        self.verbose = self.experiment.audio_low_latency_play_verbose
        if self.dummy_mode == 'no':
            self.module = self.experiment.audio_low_latency_play_module
            self.device = self.experiment.audio_low_latency_play_device
            if self.experiment.audio_low_latency_play_module == self.experiment.pyalsaaudio_module_name:
                self.buffer_size = self.experiment.audio_low_latency_play_buffer_size
                self.periods = self.experiment.audio_low_latency_play_periods
        self.period_size = self.experiment.audio_low_latency_play_period_size
        self.period_time_exact = self.experiment.audio_low_latency_play_period_time_exact
        self.period_time = self.experiment.audio_low_latency_play_period_time
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

        self.experiment.var.audio_low_latency_play_key_presses = ''
        self.experiment.var.audio_low_latency_play_key_timestamps = ''

    def _check_init(self):
        if not hasattr(self.experiment, 'audio_low_latency_play_device'):
            raise OSException('Audio Low Latency Play Init item is missing')

    def _show_message(self, message):
        oslogger.debug(message)
        if self.verbose == 'yes':
            print(message)

    def _set_stimulus_onset(self, time=None):
        if time is None:
            time = self.clock.time()
        self.experiment.var.set(f"time_stimulus_onset_{self.name}", time)
        return time

    def _set_stimulus_offset(self, time=None):
        if time is None:
            time = self.clock.time()
        self.experiment.var.set(f"time_stimulus_offset_{self.name}", time)
        return time

    def _set_stimulus_timing(self, _type, time=None):
        if time is None:
            time = self.clock.time()
        self.experiment.var.set(f"time_stimulus_{_type}_{self.name}", time)
        return time


class QtAudioLowLatencyPlay(AudioLowLatencyPlay, QtAutoPlugin):

    def __init__(self, name, experiment, script=None):
        AudioLowLatencyPlay.__init__(self, name, experiment, script)
        QtAutoPlugin.__init__(self, __file__)
