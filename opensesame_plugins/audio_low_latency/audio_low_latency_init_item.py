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

import ctypes
import os
import re
import sys

import pygame

from libopensesame.exceptions import OSException
from libopensesame.oslogging import oslogger

from .audio_low_latency_item import AudioLowLatencyItem, PYALSAAUDIO, PYAUDIO, SOUNDDEVICE

MODULES_ENABLED = ['alsaaudio', 'sounddevice', 'pyaudio']
# Seconds to wait for a background thread to stop at the end of the experiment
THREAD_STOP_TIMEOUT = 10
SOUNDDEVICE_FORMATS = {8: 'uint8', 16: 'int16', 24: 'int24', 32: 'int32'}
# Sound cards and their PCM devices (Linux)
ASOUND_PATH = '/proc/asound'
# Suffixes of the PCM names of HD Audio codecs (generic parser)
HDA_PCM_SUFFIXES = (' Alt Analog', ' Analog', ' Digital')
# The ALSA devices of PortAudio, e.g. 'M2: USB Audio (hw:1,0)'
PORTAUDIO_HW_DEVICE = r'\(hw:(\d+),(\d+)\)$'


class AudioLowLatencyInitItem(AudioLowLatencyItem):
    """Base class of the play init and record init items: opens the audio
    device and stores the settings on the experiment (see
    audio_low_latency_item.py).
    """

    def _set_var(self, name, value):
        self.experiment.var.set(f'audio_low_latency_{self.kind}_{name}', value)

    def reset(self):
        self.verbose = 'yes'
        self.var.dummy_mode = 'no'
        self.var.verbose = 'yes'
        self.var.bitdepth = 16
        self.var.samplerate = 44100
        self.var.channels = 2
        self.var.period_size = 1024
        self.var.periods = 4

        self.pyalsaaudio_module_name = PYALSAAUDIO
        self.pyaudio_module_name = PYAUDIO
        self.sounddevice_module_name = SOUNDDEVICE
        self.experiment.pyalsaaudio_module_name = PYALSAAUDIO
        self.experiment.sounddevice_module_name = SOUNDDEVICE
        self.experiment.pyaudio_module_name = PYAUDIO

        devices = {}
        if os.name == 'posix' and 'alsaaudio' in MODULES_ENABLED:
            devices[PYALSAAUDIO] = self._alsa_devices()
        if 'sounddevice' in MODULES_ENABLED:
            devices[SOUNDDEVICE] = self._sounddevice_devices()
        if 'pyaudio' in MODULES_ENABLED:
            devices[PYAUDIO] = self._pyaudio_devices()
        # Only modules with devices, in the order of preference
        self._set('module_list', [])
        self._set('device_dict', {})
        self._set('device_selected_dict', {})
        for module in (PYALSAAUDIO, SOUNDDEVICE, PYAUDIO):
            if devices.get(module):
                self._get('module_list').append(module)
                self._get('device_dict')[module] = devices[module]
                self._get('device_selected_dict')[module] = devices[module][0]

        self._show_message(f'Audio Low Latency {self._title} plug-in has been initialized!')

        module_list = self._get('module_list')
        self.var.module = module_list[0] if module_list else ''
        self.var.device_name = self._get('device_dict').get(self.var.module, [''])[0]

    def _alsa_devices(self):
        try:
            import alsaaudio
        except ImportError:
            self._show_message('Could not import alsaaudio')
            return []
        return alsaaudio.pcms(alsaaudio.PCM_PLAYBACK if self.kind == 'play' else alsaaudio.PCM_CAPTURE)

    def _sounddevice_devices(self):
        try:
            import sounddevice
            return [card['name'] for card in sounddevice.query_devices()]
        except (ImportError, OSError) as e:
            # sounddevice raises an OSError when the PortAudio library is missing
            self._show_message(f'Could not import sounddevice: {e}')
            return []

    def _pyaudio_devices(self):
        try:
            import pyaudio
        except ImportError:
            self._show_message('Could not import pyaudio')
            return []
        pyaudio_device = pyaudio.PyAudio()
        cards = [pyaudio_device.get_device_info_by_index(di)['name']
                 for di in range(pyaudio_device.get_device_count())]
        pyaudio_device.terminate()
        return cards

    def prepare(self):
        super().prepare()
        self._reset_device()
        self._init_var()

        if self.dummy_mode == 'no':
            self._show_message(f'\nChosen {self._activity} parameters:\n')
            self._show_message(f'Module: {self.module}')
            self._show_message(f'Device: {self.device_name}')
            self._show_message(f'Bitdepth: {self.bitdepth}bit')
            self._show_message(f'Samplerate: {self.samplerate}Hz')
            self._show_message(f'Channels: {self.channels}')
            self._show_message(f'Period size: {self.period_size} frames')
            self._show_message(f'Period time: {self.period_time} ms')
            if self.module == PYALSAAUDIO:
                self._show_message(f'Buffer size: {self.buffer_size} frames')
                self._show_message(f'Number of periods per buffer: {self.periods}')
            self._show_message('')

            try:
                pygame.mixer.stop()
                pygame.mixer.quit()
                self._show_message('Stopped pygame mixer')
            except pygame.error:
                self._show_message('pygame mixer not active')

            module_list = self._get('module_list')
            if self.module not in module_list:
                raise OSException(f'Module {self.module} is not available\n\n'
                                  f'Available modules: {", ".join(module_list)}')
            device_list = self._get('device_dict')[self.module]
            if self.device_name not in device_list:
                raise OSException(f'Device {self.device_name} is not available for module {self.module}\n\n'
                                  f'Available devices: {", ".join(device_list)}')
            self.device_index = device_list.index(self.device_name)

            if self.module == PYALSAAUDIO:
                self._open_alsa()
            elif self.module == PYAUDIO:
                self._open_pyaudio()
            elif self.module == SOUNDDEVICE:
                self._open_sounddevice()

            self._set('device', self.device)
            soundcard = self._soundcard()
            self._show_message(f'Sound card: {soundcard}')
            self._set_var('soundcard', soundcard)
            self._log_actual_sizes()
            if self.module != PYALSAAUDIO:
                self._log_portaudio_latency()
            self.experiment.cleanup_functions.append(self.close)
        elif self.dummy_mode == 'yes':
            self._set('device', None)
            self._set_var('soundcard', 'dummy mode')
            self._set_var('period_size_actual', 'dummy mode')
            self._set_var('buffer_size_actual', 'dummy mode')
            if self.module != PYALSAAUDIO:
                self._set_var('portaudio_latency', 'dummy mode')
            self._show_message('Dummy mode enabled, run phase')
        else:
            raise OSException(f'Dummy mode should be yes or no, not {self.dummy_mode}')

    def _open_alsa(self):
        import alsaaudio

        formats = {8: alsaaudio.PCM_FORMAT_U8,
                   16: alsaaudio.PCM_FORMAT_S16_LE,
                   # Packed 24 bit, as in a wave file (S24_LE has 4 bytes per sample)
                   24: alsaaudio.PCM_FORMAT_S24_3LE,
                   32: alsaaudio.PCM_FORMAT_S32_LE}
        try:
            self.device = alsaaudio.PCM(type=alsaaudio.PCM_PLAYBACK if self.kind == 'play' else alsaaudio.PCM_CAPTURE,
                                        format=formats[self.bitdepth],
                                        device=self.device_name,
                                        channels=self.channels,
                                        rate=self.samplerate,
                                        periodsize=self.period_size,
                                        periods=self.periods)
        except alsaaudio.ALSAAudioError as e:
            raise OSException(f'Could not open audio device {self.device_name}\n\nMessage: {e}')

        self._show_message('Audio device opened')

        # The parameters that ALSA reports for this device
        device_info = self.device.info()
        error_msg_list = []
        if device_info['physical_bits'] != self.bitdepth:
            error_msg_list.append(f'Bit depth of {self.bitdepth} bit not supported. {device_info["physical_bits"]} bit is recommended.\n')
        if device_info['period_size'] != self.period_size:
            error_msg_list.append(f'Period size of {self.period_size} frames not supported. {device_info["period_size"]} frames is recommended.\n')
        if device_info['periods'] != self.periods:
            error_msg_list.append(f'Number of periods per buffer of {self.periods} not supported. factor of {device_info["periods"]} is recommended.\n')
        if device_info['channels'] != self.channels:
            error_msg_list.append(f'{self.channels} channel(s) not supported. {device_info["channels"]} channel(s) is recommended.\n')
        if device_info['rate'] != self.samplerate:
            error_msg_list.append(f'Samplerate of {self.samplerate} Hz not supported. {device_info["rate"]} Hz is recommended.\n\n')
        if error_msg_list:
            raise OSException(f'Error with device: {self.device_name}\n{"".join(error_msg_list)}')

        # The parameters that the hardware uses, for hw: and plughw: devices
        hw_params = self._read_hw_params()
        if hw_params is None:
            self._show_message('Could not verify parameters within Linux')
            return
        real_buffer_size, real_period_size, real_channels, real_samplerate = hw_params
        real_periods = int(real_buffer_size / real_period_size)
        error_msg_list = []
        if real_period_size != self.period_size:
            error_msg_list.append(f'Period size of {self.period_size} frames not supported. {real_period_size} frames is recommended.\n')
        else:
            self._show_message('Chosen period size is supported and use is verified')
        if real_periods != self.periods:
            error_msg_list.append(f'{self.periods} periods per buffer not supported\n')
        if real_channels != self.channels:
            error_msg_list.append(f'{self.channels} channel(s) not supported\n')
        if real_samplerate != self.samplerate:
            error_msg_list.append(f'Samplerate of {self.samplerate} Hz not supported\n')
        if error_msg_list:
            raise OSException(f'Error with device: {self.device_name}\n{"".join(error_msg_list)}')

    def _soundcard(self):
        """Returns the name of the sound card of the opened device, e.g.
        'MOTU M2' or 'Realtek ALC1220', or 'unknown' (e.g. a sound server).
        """
        if self.module == PYALSAAUDIO:
            # -1 when the device is not on a sound card (e.g. pipewire, null)
            device_info = self.device.info()
            return self._alsa_soundcard(device_info['card_no'], device_info['device_no'])
        if sys.platform.startswith('linux'):
            hw = re.search(PORTAUDIO_HW_DEVICE, self.device_name)
            if hw:
                return self._alsa_soundcard(int(hw.group(1)), int(hw.group(2)))
            return 'unknown'
        # Windows and macOS: the device name holds the card, e.g.
        # 'Speakers (Realtek(R) Audio)'
        return self.device_name

    def _alsa_soundcard(self, card, device):
        """Returns the HD Audio codec of the PCM device (e.g. 'Realtek
        ALC1220'), else the long name of the card without its address
        (e.g. 'MOTU M2', 'HDA Intel PCH'), else 'unknown'.
        """
        if card < 0:
            return 'unknown'
        direction = 'p' if self.kind == 'play' else 'c'
        card_path = os.path.join(ASOUND_PATH, f'card{card}')
        try:
            # e.g. "id: ALC1220 Analog"
            with open(os.path.join(card_path, f'pcm{device}{direction}', 'info')) as f:
                pcm_info = dict(line.rstrip('\n').split(': ', 1) for line in f if ': ' in line)
            pcm_id = pcm_info['id']
            for suffix in HDA_PCM_SUFFIXES:
                if pcm_id.endswith(suffix):
                    chip = pcm_id[:-len(suffix)]
                    for filename in sorted(os.listdir(card_path)):
                        if not filename.startswith('codec#'):
                            continue
                        # e.g. "Codec: Realtek ALC1220"
                        with open(os.path.join(card_path, filename)) as f:
                            codec = f.readline().rstrip('\n').partition('Codec: ')[2]
                        if re.search(rf'(^| ){re.escape(chip)}( |$)', codec):
                            return codec
                    break
        except (OSError, KeyError, ValueError):
            pass
        try:
            # e.g. " 1 [M2             ]: USB-Audio - M2", then the long name
            # "MOTU M2 at usb-0000:00:14.0-2, high speed" on the next line
            with open(os.path.join(ASOUND_PATH, 'cards')) as f:
                lines = f.read().splitlines()
            for line, next_line in zip(lines, lines[1:]):
                if re.match(rf'\s*{card} \[', line):
                    longname = next_line.strip()
                    return longname.rpartition(' at ')[0] if ' at ' in longname else longname
        except OSError:
            pass
        return 'unknown'

    def _log_actual_sizes(self):
        """Logs the period size and buffer size that the sound card (Linux)
        or WASAPI (Windows, SoundDevice: buffer size only) uses, 'unknown'
        when the system doesn't report it. PortAudio: a period size other
        than the chosen one is a warning.
        """
        period_size, buffer_size = 'unknown', 'unknown'
        if sys.platform.startswith('linux'):
            hw_params = self._read_hw_params()
            if hw_params is not None:
                buffer_size, period_size = hw_params[0], hw_params[1]
        elif sys.platform == 'win32' and self.module == SOUNDDEVICE:
            buffer_size = self._wasapi_buffer_size()
        self._show_message(f'Actual period size (frames): {period_size}')
        self._show_message(f'Actual buffer size (frames): {buffer_size}')
        if self.module != PYALSAAUDIO and period_size not in ('unknown', self.period_size):
            oslogger.warning(f'the sound card uses a period size of {period_size} frames instead of {self.period_size}')
        self._set_var('period_size_actual', period_size)
        self._set_var('buffer_size_actual', buffer_size)

    def _log_portaudio_latency(self):
        """Logs the latency in ms that PortAudio reports for the stream."""
        if self.module == SOUNDDEVICE:
            latency = self.device.latency
        elif self.kind == 'play':
            latency = self.device.get_output_latency()
        else:
            latency = self.device.get_input_latency()
        # PortAudio reports the latency in seconds
        latency = latency * 1000
        self._show_message(f'PortAudio latency: {latency} ms')
        self._set_var('portaudio_latency', latency)

    def _wasapi_buffer_size(self):
        """Returns the size in frames of the WASAPI buffer of a SoundDevice
        stream, or 'unknown' for the other Windows host APIs.
        """
        import sounddevice

        hostapi = sounddevice.query_hostapis(sounddevice.query_devices(self.device_index)['hostapi'])
        if hostapi['name'] != 'Windows WASAPI':
            return 'unknown'
        # Not in the API of SoundDevice: call PortAudio with the PaStream
        # pointer of the stream
        try:
            get_frames = ctypes.CDLL(sounddevice._libname).PaWasapi_GetFramesPerHostBuffer
            get_frames.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_uint), ctypes.POINTER(ctypes.c_uint)]
            get_frames.restype = ctypes.c_int
            stream = int(sounddevice._ffi.cast('uintptr_t', self.device._ptr))
            frames_in, frames_out = ctypes.c_uint(), ctypes.c_uint()
            error = get_frames(stream, ctypes.byref(frames_in), ctypes.byref(frames_out))
        except (AttributeError, OSError) as e:
            oslogger.warning(f'could not read the WASAPI buffer size: {e}')
            return 'unknown'
        if error:
            oslogger.warning(f'could not read the WASAPI buffer size: PortAudio error {error}')
            return 'unknown'
        return frames_out.value if self.kind == 'play' else frames_in.value

    def _hw_pcm(self):
        """Returns the card and the PCM device number of the device, as in
        /proc/asound/<card>/pcm<device><p|c>, or None.
        """
        if self.module == PYALSAAUDIO:
            card = re.search("CARD=(.*?),", self.device_name)
            if not card:
                return None
            device_number = re.search(r'DEV=(\d+)', self.device_name)
            return card.group(1), device_number.group(1) if device_number else '0'
        hw = re.search(PORTAUDIO_HW_DEVICE, self.device_name)
        if not hw:
            return None
        return f'card{hw.group(1)}', hw.group(2)

    def _read_hw_params(self):
        """Returns buffer size, period size, channels and sample rate from
        /proc/asound/<card>/pcm<device><p|c>/sub0/hw_params, or None.
        """
        pcm = self._hw_pcm()
        if pcm is None:
            return None
        card, device_number = pcm
        direction = 'p' if self.kind == 'play' else 'c'
        filename_alsa = os.path.join(ASOUND_PATH, card, f'pcm{device_number}{direction}', 'sub0', 'hw_params')
        try:
            with open(filename_alsa) as f:
                params = dict(line.split(':', 1) for line in f if ':' in line)
            # e.g. "rate: 44100 (44100/1)"
            return (int(params['buffer_size']), int(params['period_size']),
                    int(params['channels']), int(params['rate'].split()[0]))
        except (OSError, KeyError, ValueError, IndexError):
            # e.g. "closed" when another program changed the device
            return None

    def _open_pyaudio(self):
        import pyaudio

        # Sample width 4 is float32 in PyAudio
        if self.bitdepth == 32:
            raise OSException(f'{self.bitdepth} bit audio is not supported by PyAudio')
        self.device_init = pyaudio.PyAudio()
        try:
            if self.kind == 'play':
                direction = dict(output=True, output_device_index=self.device_index)
            else:
                direction = dict(input=True, input_device_index=self.device_index)
            self.device = self.device_init.open(format=self.device_init.get_format_from_width(self.samplewidth),
                                                channels=self.channels,
                                                rate=self.samplerate,
                                                frames_per_buffer=self.period_size,
                                                **direction)
            self._show_message("Audio device opened")
        except Exception as e:
            self.device_init.terminate()
            del self.device_init
            raise OSException(f'Could not open audio device {self.device_name}\n\nMessage: {e}')

        if self.kind == 'play':
            self._show_message(f'Frames available for writing: {self.device.get_write_available()}')

    def _open_sounddevice(self):
        import sounddevice

        stream_class = sounddevice.RawOutputStream if self.kind == 'play' else sounddevice.RawInputStream
        try:
            self.device = stream_class(samplerate=float(self.samplerate),
                                       dtype=SOUNDDEVICE_FORMATS[self.bitdepth],
                                       blocksize=int(self.period_size),
                                       device=int(self.device_index),
                                       channels=int(self.channels))
            self._show_message("Audio device opened")
            self.device.start()
        except Exception as e:
            raise OSException(
                f'Could not start audio device\n\nMessage: {e}')

    def close(self):
        self._stop_thread()
        self._reset_device()

    def _stop_thread(self):
        # A background playback or recording that is still running (e.g. after
        # an error or a user abort) uses the device: stop it before closing
        # the device
        thread = self._get('thread', None)
        if thread is None:
            return
        if thread.is_alive():
            self._show_message(f'Stopping background audio {self._activity}')
            self._set('continue', 0)
            self._set('execute_pause', 0)
            thread.join(THREAD_STOP_TIMEOUT)
            if thread.is_alive():
                oslogger.warning(f'background audio {self._activity} did not stop')
        # An error that no wait or stop item has raised (e.g. it was skipped)
        error = self._get('thread_error', None)
        if error is not None:
            oslogger.warning(f'background audio {self._activity} failed: {error}')

    def _init_var(self):
        self.dummy_mode = self.var.dummy_mode
        self.verbose = self.var.verbose
        self.module = self.var.module
        self.device_name = self.var.device_name

        self.period_size = self._positive_int('period_size', 'Period size value')
        self.samplerate = self._positive_int('samplerate', 'Sample rate value')
        self.channels = self._positive_int('channels', 'Channel value')
        self.periods = self._positive_int('periods', 'Number of periods per buffer value')

        if not isinstance(self.var.bitdepth, int):
            raise OSException('Bit depth should be an integer')
        if self.var.bitdepth not in (8, 16, 24, 32):
            raise OSException('Bit depth should be 8, 16, 24 or 32')
        self.bitdepth = self.var.bitdepth
        self.samplewidth = int(self.bitdepth / 8)

        self.buffer_size = int(self.period_size * self.periods)
        self.frame_size = int(self.samplewidth * self.channels)
        self.data_size = int(self.frame_size * self.period_size)
        self.period_time_exact = float(self.period_size) / float(self.samplerate) * 1000
        self.period_time = round(self.period_time_exact, 1)

        self._set('dummy_mode', self.dummy_mode)
        self._set('verbose', self.verbose)
        self._set('locked', 0)
        self._set('module', self.module)
        self._set('bitdepth', self.bitdepth)
        self._set('samplewidth', self.samplewidth)
        self._set('samplerate', self.samplerate)
        self._set('channels', self.channels)
        self._set('period_size', self.period_size)
        self._set('data_size', self.data_size)
        self._set('period_time_exact', self.period_time_exact)
        self._set('period_time', self.period_time)
        if self.module == PYALSAAUDIO:
            self._set('buffer_size', self.buffer_size)
            self._set('periods', self.periods)
            self._set('buffer_time', round(self.periods * self.period_time, 1))

        self._set_var('module', self.module)
        self._set_var('device_name', self.device_name)
        self._set_var('period_size', self.period_size)
        self._set_var('period_time_exact', self.period_time_exact)
        self._set_var('period_time', self.period_time)
        if self.module == PYALSAAUDIO:
            self._set_var('buffer_size', self.buffer_size)
            self._set_var('periods', self.periods)
            self._set_var('buffer_time', self._get('buffer_time'))
        self._set_var('bitdepth', self.bitdepth)
        self._set_var('samplewidth', self.samplewidth)
        self._set_var('samplerate', self.samplerate)
        self._set_var('channels', self.channels)

        # reset experimental variables
        self._set('background', None)
        self._set('thread_running', 0)

    def _positive_int(self, name, label):
        value = getattr(self.var, name)
        if not isinstance(value, int) or value <= 0:
            raise OSException(f'{label} should be a positive integer')
        return value

    def _reset_device(self):
        if not hasattr(self.experiment, f'audio_low_latency_{self.kind}_device'):
            self._show_message("no active Audio Device")
            return
        device = self._get('device')
        if device is None:
            # dummy mode
            delattr(self.experiment, f'audio_low_latency_{self.kind}_device')
            return
        try:
            self._show_message("Closing audio device")
            if self.module == PYAUDIO:
                device.stop_stream()
                device.close()
                self.device_init.terminate()
                del self.device_init
            else:
                device.close()

            delattr(self.experiment, f'audio_low_latency_{self.kind}_device')
            del self.device
            self._show_message("Audio device closed")
        except Exception as e:
            oslogger.warning(f'failed to close audio device: {e}')
