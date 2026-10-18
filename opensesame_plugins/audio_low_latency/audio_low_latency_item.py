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

Shared code of the Audio Low Latency items.

The items share their state on the experiment, as
experiment.audio_low_latency_<kind>_<name>, where kind is play or record.
Inline scripts may use these attributes: keep their names and types.

- Set by the init item: device (None in dummy mode), dummy_mode and verbose
  ('yes'/'no'), module, bitdepth, samplewidth, samplerate, channels,
  period_size, data_size, period_time, period_time_exact, for PyAlsaAudio
  also buffer_size, periods and buffer_time; module_list, device_dict and
  device_selected_dict (devices per module, for the GUI); locked and
  thread_running (0/1).
- Set by the start item: thread, thread_error (exception of the thread, or
  None), continue and execute_pause (0/1), pause_resume_key (the pause/resume
  keys as entered).
- start, stop, wait, pause and resume: True when that item has been prepared,
  so that the items can check that the others exist.
"""

__author__ = "Bob Rosbag"
__license__ = "GPLv3"

import os
import threading
import time

from libopensesame.item import Item
from libopensesame.exceptions import OSException
from libopensesame.oslogging import oslogger
from openexp.keyboard import Keyboard

from .win_keyboard import WinKeyboard

PYALSAAUDIO = 'PyAlsaAudio (Linux only)'
SOUNDDEVICE = 'SoundDevice (PortAudio)'
PYAUDIO = 'PyAudio (PortAudio)'

# Debug tool: 1 prints the time of every period at the end, 2 prints it
# right away
TIMESTAMP = 0
# Seconds between two checks of a paused playback or recording without keys
PAUSE_POLL_TIME = 0.001


class AudioLowLatencyItem(Item):
    """Base class of all items except the init items."""

    # 'play' or 'record'
    kind = None

    @property
    def _title(self):
        return 'Play' if self.kind == 'play' else 'Record'

    @property
    def _activity(self):
        return 'playback' if self.kind == 'play' else 'recording'

    def _get(self, name, *default):
        return getattr(self.experiment, f'audio_low_latency_{self.kind}_{name}', *default)

    def _set(self, name, value):
        setattr(self.experiment, f'audio_low_latency_{self.kind}_{name}', value)

    def _check_init(self):
        if not hasattr(self.experiment, f'audio_low_latency_{self.kind}_device'):
            raise OSException(f'`Audio Low Latency {self._title} Init` item is missing')

    def _check_start(self):
        if not self._get('start', False):
            raise OSException(f'`Audio Low Latency {self._title} Start` item is missing')

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


class AudioLowLatencyControlItem(AudioLowLatencyItem):
    """Base class of the stop, wait, pause and resume items, which control
    the thread of the start item.
    """

    # 'stop', 'wait', 'pause' or 'resume'
    role = None

    def prepare(self):
        super().prepare()
        self._check_init()
        self.dummy_mode = self._get('dummy_mode')
        self.verbose = self._get('verbose')
        self._set(self.role, True)

    def run(self):
        self._check_start()
        if self.role in ('pause', 'resume'):
            self._check_pause_resume()
        self.set_item_onset()

        if self.dummy_mode == 'no':
            if not self._get('thread_running'):
                raise OSException(
                    f'`Audio Low Latency {self._title} Start` did not run before this item')
            self._control()
        else:
            self._show_message(f'Dummy mode enabled, NOT {"playing" if self.kind == "play" else "recording"} audio')

    def _control(self):
        raise NotImplementedError

    def _check_pause_resume(self):
        other = 'resume' if self.role == 'pause' else 'pause'
        if not self._get('pause_resume_key') and not self._get(other):
            raise OSException(f'`Audio Low Latency {self._title} {self.role.capitalize()}` '
                              'item is missing a resume/pause key or item')

    def _join_thread(self):
        self._get('thread').join()
        self._set('thread_running', 0)
        error = self._get('thread_error')
        if error is not None:
            self._set('thread_error', None)
            if isinstance(error, OSException):
                raise error
            raise OSException(
                f'Background audio {self._activity} failed\n\nMessage: {error}') from error


class AudioLowLatencyStreamItem(AudioLowLatencyItem):
    """Base class of the play, play start, record and record start items."""

    # True for the start items, which play or record in a thread
    background = False
    # ms between two checks whether another playback or recording has ended
    lock_poll_time = 1

    def _init_var(self):
        self.dummy_mode = self._get('dummy_mode')
        self.verbose = self._get('verbose')
        if self.dummy_mode == 'no':
            self.module = self._get('module')
            self.device = self._get('device')
            if self.module == PYALSAAUDIO:
                self.buffer_size = self._get('buffer_size')
                self.periods = self._get('periods')
        self.period_size = self._get('period_size')
        self.period_time_exact = self._get('period_time_exact')
        self.period_time = self._get('period_time')
        self.data_size = self._get('data_size')
        self.bitdepth = self._get('bitdepth')
        self.samplewidth = self._get('samplewidth')
        self.samplerate = self._get('samplerate')
        self.channels = self._get('channels')

    def _init_keys(self):
        self.pause_resume = self.var.pause_resume
        self.stop = self.var.stop
        if self.background:
            self._set('pause_resume_key', self.pause_resume)
            self._set('continue', 1)
            self._set('start', True)
            self._set('execute_pause', 0)
            for role in ('stop', 'wait', 'pause', 'resume'):
                self._set(role, False)
            self._key_log = f'audio_low_latency_{self.kind}_start'
        else:
            self._key_log = f'audio_low_latency_{self.kind}'
        self._flags = {'continue': 1, 'execute_pause': 0}
        self.experiment.var.set(f'{self._key_log}_key_presses', '')
        self.experiment.var.set(f'{self._key_log}_key_timestamps', '')

        self.kb = Keyboard(self.experiment, timeout=1)
        self._allowed_responses_pause_resume = self._parse_keys(self.pause_resume, 'Pause/resume')
        self._allowed_responses_stop = self._parse_keys(self.stop, 'Stop')
        self._keylist = self._allowed_responses_pause_resume + self._allowed_responses_stop
        # The keyboard can't be read in a thread under Windows
        self._win_keyboard = None
        if self.background and os.name == 'nt' and self._keylist:
            self._win_keyboard = WinKeyboard(self.clock, self._keylist)

    def _parse_keys(self, keys, label):
        if keys == '':
            return []
        allowed = [key.strip() for key in str(keys).split(';') if key.strip() != '']
        if not allowed:
            raise OSException(f'{label} keys should be a semicolon-separated list of keys, e.g. a;b;c')
        self._show_message(f"allowed {label.lower()} keys set to {allowed}")
        return allowed

    def _check_delay(self, name, label):
        value = getattr(self.var, name)
        if not isinstance(value, int):
            raise OSException(f'{label} should be a integer')
        if value < 0:
            raise OSException(f'{label} can not be negative')
        return value

    def _check_ram_cache(self, label):
        self.ram_cache = self.var.ram_cache
        if self.ram_cache not in ('yes', 'no'):
            raise OSException(f'{label} should be yes or no, not {self.ram_cache}')

    def _check_stop_wait(self):
        if not self._get('stop') and not self._get('wait'):
            raise OSException(f'`Audio Low Latency {self._title} Stop` or '
                              f'`Audio Low Latency {self._title} Wait` item is missing')

    def _wait_until_unlocked(self):
        while self._get('locked'):
            self.clock.sleep(self.lock_poll_time)

    def _start_keys(self):
        if self._win_keyboard is not None:
            self._win_keyboard.flush()
        elif self._keylist:
            self.kb.flush()

    # The foreground items keep the stop and pause signals themselves, the
    # background items on the experiment, where the stop and pause items
    # can change them.
    def _flag(self, name):
        if self.background:
            return self._get(name)
        return self._flags[name]

    def _set_flag(self, name, value):
        if self.background:
            self._set(name, value)
        else:
            self._flags[name] = value

    def _start_thread(self, target, args):
        thread = threading.Thread(target=self._run_thread, args=(target,) + args)
        self._set('thread', thread)
        self._set('locked', 1)
        self._set('thread_error', None)
        self._set('continue', 1)
        self._set('execute_pause', 0)
        self._set('thread_running', 1)
        thread.start()

    def _run_thread(self, target, *args):
        # An exception in a thread is only printed: store it, the wait or
        # stop item raises it
        try:
            target(*args)
        except Exception as e:
            self._show_message(f'Error in background {self._activity}: {e}')
            self._set('thread_error', e)
        finally:
            self._set('locked', 0)

    def _sleep(self, ms):
        if self.background:
            # clock.sleep() needs pyglet.app in the thread under Windows
            target_time = time.perf_counter() + (ms / 1000.0)
            while time.perf_counter() < target_time:
                time.sleep(0.001)
        else:
            self.clock.sleep(ms)

    def _wait_while_paused(self, stream, drop_on_duration=False):
        """Waits until resumed or stopped; returns the pause duration (ms).

        With drop_on_duration (playback), a pause that lasts until the
        duration stops the playback without resuming it: ALSA drops the
        queued audio (self.dropped).
        """
        self._show_message(f'Paused audio {self._activity}')
        pause_start_time = self.clock.time()
        if self.module == PYALSAAUDIO:
            stream.pause(True)
        while self._paused():
            if self._keylist:
                self._check_keys()
            else:
                time.sleep(PAUSE_POLL_TIME)
            if self.duration_check:
                if self._check_duration():
                    break
        if drop_on_duration and self.duration_exceeded:
            if self.module == PYALSAAUDIO:
                stream.drop()
                self.dropped = True
            self._show_message(f'Stopped paused audio {self._activity}')
        else:
            if self.module == PYALSAAUDIO:
                stream.pause(False)
            self._show_message(f'Resumed audio {self._activity}')
        return self.clock.time() - pause_start_time

    def _paused(self):
        return self._flag('execute_pause') == 1 and self._flag('continue') == 1

    def _check_keys(self):
        # Pass the key list on every call: the psycho backend adds 'escape'
        # to a stored key list each time get_key() is called
        if self._win_keyboard is not None:
            key1, time1 = self._win_keyboard.get_key()
        else:
            key1, time1 = self.kb.get_key(keylist=self._keylist)
            self.kb.flush()
        if key1 in self._allowed_responses_stop:
            self._show_message('Detected key press for stopping audio')
            self._log_keys(key1, str(time1))
            self._set_flag('continue', 0)
        if key1 in self._allowed_responses_pause_resume:
            self._log_keys(key1, str(time1))
            if self._flag('execute_pause') == 0:
                self._show_message(f'Detected key press for pausing audio {self._activity}')
                self._set_flag('execute_pause', 1)
            elif self._flag('execute_pause') == 1:
                self._show_message(f'Detected key press for resuming audio {self._activity}')
                self._set_flag('execute_pause', 0)

    def _log_keys(self, key1, time1):
        for name, value in (('key_presses', key1), ('key_timestamps', time1)):
            var = f'{self._key_log}_{name}'
            self.experiment.var.set(var, getattr(self.experiment.var, var) + f"{value};")

    def _check_duration(self):
        if self.clock.time() - self.start_time >= self.duration:
            self._show_message(f'Stopping audio {self._activity}, duration exceeded')
            self.duration_exceeded = True
            return True
        else:
            return False
