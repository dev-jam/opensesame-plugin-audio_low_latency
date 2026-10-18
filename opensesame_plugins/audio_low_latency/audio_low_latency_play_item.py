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

import wave

from libopensesame.exceptions import OSException
from libopensesame.oslogging import oslogger

from .audio_low_latency_item import AudioLowLatencyStreamItem, PYALSAAUDIO, TIMESTAMP

# Fill the last period with silence, so every write is a whole period
PADDING = True


class AudioLowLatencyPlayItem(AudioLowLatencyStreamItem):
    """Base class of the play (foreground) and play start (background)
    items.
    """

    kind = 'play'

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
        self.filename = self.experiment.pool[self.var.filename]
        self._check_ram_cache('Preload')
        self._init_keys()
        self.delay = self._check_delay('delay', 'Delay')
        self.delay_check = self.delay > 0

        if self.dummy_mode == 'no':
            self._load_file()
        else:
            if not self.background:
                self._set_stimulus_onset()
            self._show_message('Dummy mode enabled, prepare phase')

    def _load_file(self):
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
        if self.module == PYALSAAUDIO:
            n_buffers = round(n_periods / self.periods, 2)
            self._show_message(f"Buffer consists: {self.periods} periods")
            self._show_message(f"Number of buffers to be played: {n_buffers} buffers")
        self._show_message('')

        error_msg = 'Duration must be a string named sound or a an integer greater than 1'
        if self.var.duration == 'sound':
            self.duration_check = False
            self.duration = self.wav_duration
        elif isinstance(self.var.duration, int) and self.var.duration >= 1:
            self.duration_check = True
            self.duration = self.var.duration
        else:
            raise OSException(error_msg)

        if self.ram_cache == 'yes':
            self._show_message('Loading wave file into cache...')
            self.wav_file_data = self.wav_file.readframes(wav_file_nframes)
            self._show_message('Done! Closing wave file...')
            self.wav_file.close()
        else:
            self._show_message('Reading directly from wave file, no cache')

    def run(self):
        if self.background:
            self._check_stop_wait()
        self.set_item_onset()
        _start_time = self.clock.time()

        if self.dummy_mode == 'no':
            self._wait_until_unlocked()
            if self.delay_check:
                time_passed = self.clock.time() - _start_time
                delay = round(self.delay - time_passed, 1)
            else:
                delay = self.delay
            self._start_keys()
            self._show_message('Initializing audio playback')
            if self.ram_cache == 'no':
                args = (self.device, self.wav_file, self.period_size, delay)
            else:
                args = (self.device, self.wav_file, self.data_size, delay, self.wav_file_data)
            if self.background:
                self._start_thread(self._play, args)
            else:
                self._play(*args)
        else:
            self._set_stimulus_onset()
            self._show_message('Dummy mode enabled, NOT playing audio')

    def _play(self, stream, wav_file, chunk, delay, wav_data=None):
        period = 0
        pause_duration = 0
        underruns = 0

        self.duration_exceeded = False

        if self.ram_cache == 'no':
            data = wav_file.readframes(chunk)
        else:
            start = 0
            data = wav_data[start:start+chunk]
            start += chunk
        data_length = len(data)
        self._show_message(f"Chunk size: {data_length} bytes")
        if self.delay_check:
            if delay >= 1:
                self._show_message(f"Delaying audio playback for {delay} ms")
                self._sleep(delay)
                self._show_message('Delay done')
        self.start_time = self._set_stimulus_onset()
        self._show_message('Starting audio playback')

        if TIMESTAMP == 1:
            timestamp_list = []
            timestamp_list.append(str(self.clock.time()))
        elif TIMESTAMP == 2:
            self._show_message(self.clock.time())

        while len(data) > 0:

            result = stream.write(data)
            # PyAlsaAudio returns -EPIPE after an underrun: this period was not played
            if self.module == PYALSAAUDIO and result < 0:
                underruns += 1
            period += 1

            if TIMESTAMP == 1:
                timestamp_list.append(str(self.clock.time()))
            elif TIMESTAMP == 2:
                self._show_message(self.clock.time())

            if self.ram_cache == 'no':
                data = wav_file.readframes(chunk)
                if len(data) == 0:
                    self._show_message('Finished processing audio data')
                    break
                data_length = len(data)
            else:
                if start >= len(wav_data):
                    self._show_message('Finished processing audio data')
                    break
                data = wav_data[start:start+chunk]
                data_length = len(data)
                start += chunk

            if PADDING and data_length < self.data_size:
                self._show_message('Padding last period with silence')
                padding = self.data_size - data_length
                data = data + b'\x00' * padding

            if self._keylist:
                self._check_keys()
            if self._paused():
                pause_duration += self._wait_while_paused(stream)
            if self.duration_check and not self.duration_exceeded:
                self._check_duration()
            if self._flag('continue') == 0 or self.duration_exceeded:
                self._show_message('Stopped audio playback')
                break

        duration_processing_audio = int(round(self.clock.time() - self.start_time - pause_duration))

        if self.module == PYALSAAUDIO:
            stream.drain()
            self._show_message('Draining ALSA stream')

        self._set_stimulus_offset()

        duration_total_exact = self.clock.time() - self.start_time
        duration_playing_audio_exact = duration_total_exact - pause_duration
        duration_total = int(round(duration_total_exact))
        duration_playing_audio = int(round(duration_playing_audio_exact))
        duration_pause = int(round(pause_duration))

        if self._flag('continue') == 0:
            # Stopped by a key: don't wait for the rest of the duration
            self.experiment.var.wait_to_finish = 0
        else:
            self.experiment.var.wait_to_finish = int(round(self.duration - duration_playing_audio))
        # The background item doesn't wait: the next items run meanwhile
        if not self.background and self.experiment.var.wait_to_finish > 0:
            self._show_message(f"Waiting {self.experiment.var.wait_to_finish} ms for audio to finish")
            self._sleep(self.experiment.var.wait_to_finish)

        if self.ram_cache == 'no':
            wav_file.close()
        if underruns:
            oslogger.warning(f'{underruns} buffer underrun(s) during audio playback: '
                             f'{underruns} period(s) of the sound were not played')
        self._show_message('Finished audio playback')
        self._show_message(f"Audio file duration: {self.wav_duration} ms")
        self._show_message(f"Duration total: {duration_total} ms")
        self._show_message(f"Duration pauses: {duration_pause} ms")
        self._show_message(f"Duration processing audio: {duration_processing_audio} ms")
        self._show_message(f"Duration playing audio: {duration_playing_audio} ms")
        self._show_message('')

        if self.module == PYALSAAUDIO:
            mod_period = (period - 1) % self.periods + 1
            self._show_message(f"Number of periods played: {period}")
            self._show_message(f"Finished in period: {mod_period}")

        if TIMESTAMP == 1:
            self._show_message("\n".join(timestamp_list))

        if self.background:
            self._show_message('Unlocking thread')
            self._set('locked', 0)
