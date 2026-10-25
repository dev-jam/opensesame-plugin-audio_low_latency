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
  device_selected_dict (devices per module, for the GUI), device_index_dict
  and device_host_api_dict (the library's index and the host API of each
  device in device_dict), host_api_dict (the host APIs of SoundDevice and
  PyAudio) and unusable_device_dict (per module the devices left out: {name: host
  API}); locked and thread_running (0/1).
- Set by the start item: thread, thread_error (exception of the thread, or
  None), continue and execute_pause (0/1), pause_resume_key (the pause/resume
  keys as entered); the record start item also sets infinite (1 when it
  records without end: infinite duration and no stop key, else 0).
- start, stop, wait, pause and resume: True when that item has been prepared,
  so that the items can check that the others exist.

Variables for the log file (experiment.var), also for inline scripts:
- Set by the init item: audio_low_latency_<kind>_<name> with name module,
  device_name, period_size, period_time, period_time_exact, periods,
  buffer_size (period size times the number of periods), buffer_time (only
  PyAlsaAudio uses these three), bitdepth, samplewidth, samplerate and
  channels (_set_var() in audio_low_latency_init_item.py);
  also soundcard (e.g. 'MOTU M2' or 'Realtek ALC1220'; 'unknown' when it
  can't be found, 'dummy mode' in dummy mode), period_size_actual and
  buffer_size_actual (frames that the sound card or WASAPI uses; 'unknown'
  when the system doesn't report it, 'dummy mode' in dummy mode); for
  SoundDevice and PyAudio also portaudio_latency (ms, as PortAudio reports
  it) and host_api (of the opened device, e.g. 'Windows WASAPI'); 'dummy
  mode' in dummy mode; for SoundDevice also wasapi_exclusive ('yes' when
  exclusive mode is used, else 'no').
- Set by the play, record and start items: time_stimulus_onset_<item name>
  and time_stimulus_offset_<item name> (not in dummy mode);
  audio_low_latency_<kind>_key_presses and _key_timestamps, for the start
  items audio_low_latency_<kind>_start_key_presses and _key_timestamps (keys
  and times separated by ';').
- Set by the play and play start items: wav_duration (ms) and
  wait_to_finish (ms, not in dummy mode); one variable for all these items.
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
# Host API setting of the init items: devices of all host APIs
ALL_HOST_APIS = 'all'
WASAPI = 'Windows WASAPI'

# Debug tool: 1 prints the time of every period at the end, 2 prints it
# right away
TIMESTAMP = 0
# Seconds between two checks of a paused playback or recording
PAUSE_POLL_TIME = 0.001
# ms that a key check waits for a key during playback or recording
KEY_TIMEOUT = 1


class AudioLowLatencyItem(Item):
    """Base class of all items."""

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

    def _set_stimulus_onset(self):
        timestamp = self.clock.time()
        self.experiment.var.set(f"time_stimulus_onset_{self.name}", timestamp)
        return timestamp

    def _set_stimulus_offset(self):
        timestamp = self.clock.time()
        self.experiment.var.set(f"time_stimulus_offset_{self.name}", timestamp)
        return timestamp


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
        if self.role == 'wait':
            self._check_wait_ends()
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

    def _check_wait_ends(self):
        # Also in dummy mode. An inline script may have stopped the recording
        # (continue = 0) before this item.
        if self._get('infinite', 0) and self._get('continue', 1) == 1:
            raise OSException(
                f'`Audio Low Latency {self._title} Wait` would wait forever: the duration of '
                f'`Audio Low Latency {self._title} Start` is infinite and it has no stop key. '
                f'Use a stop key or an `Audio Low Latency {self._title} Stop` item instead')

    def _check_pause_resume(self):
        other = 'resume' if self.role == 'pause' else 'pause'
        if not self._get('pause_resume_key') and not self._get(other):
            raise OSException(f'`Audio Low Latency {self._title} {self.role.capitalize()}` '
                              'item is missing a resume/pause key or item')


class AudioLowLatencyStreamItem(AudioLowLatencyItem):
    """Base class of the play, play start, record and record start items."""

    # True for the start items, which play or record in a thread
    background = False
    # ms between two checks whether another playback or recording has ended
    lock_poll_time = 1

    def _init_var(self):
        self.dummy_mode = self._get('dummy_mode')
        self.verbose = self._get('verbose')
        self.module = self._get('module')
        if self.dummy_mode == 'no':
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
            # Not reset when already set: these items may have been prepared
            # before this one (e.g. after a later start item, or outside a loop)
            for role in ('stop', 'wait', 'pause', 'resume'):
                if not self._get(role, False):
                    self._set(role, False)
            self._key_log = f'audio_low_latency_{self.kind}_start'
        else:
            self._key_log = f'audio_low_latency_{self.kind}'
        self._flags = {'continue': 1, 'execute_pause': 0}
        self.experiment.var.set(f'{self._key_log}_key_presses', '')
        self.experiment.var.set(f'{self._key_log}_key_timestamps', '')

        self.kb = Keyboard(self.experiment, timeout=KEY_TIMEOUT)
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
            raise OSException(f'{label} should be an integer')
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
        # Not clock.sleep(): the legacy backend's pygame.time.delay() holds
        # up the thread that is playing or recording
        while self._get('locked'):
            time.sleep(self.lock_poll_time / 1000)

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
        if self._get('thread_running'):
            # The previous thread was not joined by a wait or stop item (it
            # has ended, the device is unlocked): raise its error
            self._join_thread()
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
            # Not when the experiment is ending: the display (and with it the
            # keyboard) is closed before the cleanup stops this thread
            if self.experiment.running:
                self._set('thread_error', e)
        finally:
            # Only here, at the very end: a next start item starts its thread
            # as soon as it sees the unlock
            self._show_message('Unlocking thread')
            self._set('locked', 0)

    def _sleep(self, ms):
        # The cut at the duration after a late resume can ask for a negative
        # time; whether every backend's clock.sleep() accepts that is not known
        if ms <= 0:
            return
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
                # get_key() with a timeout busy-waits (legacy backend)
                self._check_keys(timeout=0)
            # The Windows key reader sleeps itself
            if self._win_keyboard is None:
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

    def _check_keys(self, timeout=KEY_TIMEOUT):
        # Pass the key list on every call: the psycho backend adds 'escape'
        # to a stored key list each time get_key() is called
        if self._win_keyboard is not None:
            key1, time1 = self._win_keyboard.get_key()
        else:
            # No flush() afterwards: it would discard a key pressed after
            # get_key() looked at the queue
            key1, time1 = self.kb.get_key(keylist=self._keylist, timeout=timeout)
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
