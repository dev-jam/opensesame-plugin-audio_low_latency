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
import math
import os
import re
import sys

import pygame

from libopensesame.exceptions import OSException
from libopensesame.oslogging import oslogger

from .audio_low_latency_item import AudioLowLatencyItem, ALL_HOST_APIS, PYALSAAUDIO, PYAUDIO, SOUNDDEVICE, WASAPI

MODULES_ENABLED = ['alsaaudio', 'sounddevice']
# Seconds to wait for a background thread to stop at the end of the experiment
THREAD_STOP_TIMEOUT = 10
SOUNDDEVICE_FORMATS = {8: 'uint8', 16: 'int16', 24: 'int24', 32: 'int32'}
# Sound cards and their PCM devices (Linux)
ASOUND_PATH = '/proc/asound'
# Suffixes of the PCM names of HD Audio codecs (generic parser)
HDA_PCM_SUFFIXES = (' Alt Analog', ' Analog', ' Digital')
# The ALSA devices of PortAudio, e.g. 'M2: USB Audio (hw:1,0)'
PORTAUDIO_HW_DEVICE = r'\(hw:(\d+),(\d+)\)$'
# Host APIs of PortAudio that the items don't use, with the reason.
# DirectSound and WDM-KS have no blocking reading and writing (PortAudio
# 19.7.0: ReadStream() and WriteStream() of DirectSound do nothing and
# report success; WDM-KS refuses to open the stream). OSS (/dev/dsp, the
# OSS emulation of the kernel) bypasses ALSA and the sound card lookup.
NO_BLOCKING_IO = 'PortAudio can\'t play or record with it the way the items do'
UNUSABLE_HOST_APIS = {
    'Windows DirectSound': NO_BLOCKING_IO,
    'Windows WDM-KS': NO_BLOCKING_IO,
    'OSS': 'the OSS emulation bypasses ALSA; use PyAlsaAudio, or ALSA with SoundDevice'
}
# SoundDevice loads its PortAudio library with ASIO (Windows) only when this
# environment variable exists when it is imported
SD_ENABLE_ASIO = 'SD_ENABLE_ASIO'
ASIO = 'ASIO'
# PortAudio's error code paInvalidSampleRate
PA_INVALID_SAMPLE_RATE = -9997


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
        self.var.host_api = ALL_HOST_APIS
        self.var.wasapi_exclusive = 'no'

        self.pyalsaaudio_module_name = PYALSAAUDIO
        self.sounddevice_module_name = SOUNDDEVICE
        self.experiment.pyalsaaudio_module_name = PYALSAAUDIO
        self.experiment.sounddevice_module_name = SOUNDDEVICE

        # (index, name, host API) per device
        devices = {}
        if os.name == 'posix' and 'alsaaudio' in MODULES_ENABLED:
            devices[PYALSAAUDIO] = [(index, name, None) for index, name in enumerate(self._alsa_devices())]
        if 'sounddevice' in MODULES_ENABLED:
            devices[SOUNDDEVICE] = self._sounddevice_devices()
        # Only modules with devices, in the order of preference
        self._set('module_list', [])
        self._set('device_dict', {})
        self._set('device_selected_dict', {})
        # The index and host API of each device of device_dict
        self._set('device_index_dict', {})
        self._set('device_host_api_dict', {})
        # The host APIs per module (SoundDevice)
        self._set('host_api_dict', {})
        # Devices left out, with their host API, for the error message
        self._set('unusable_device_dict', {})
        for module in (PYALSAAUDIO, SOUNDDEVICE):
            usable = [device for device in devices.get(module, []) if device[2] not in UNUSABLE_HOST_APIS]
            self._get('unusable_device_dict')[module] = {name: host_api for _, name, host_api in devices.get(module, [])
                                                         if host_api in UNUSABLE_HOST_APIS}
            if usable:
                self._get('module_list').append(module)
                self._get('device_dict')[module] = [name for _, name, _ in usable]
                self._get('device_index_dict')[module] = [index for index, _, _ in usable]
                self._get('device_host_api_dict')[module] = [host_api for _, _, host_api in usable]
                if module != PYALSAAUDIO:
                    self._get('host_api_dict')[module] = list(dict.fromkeys(host_api for _, _, host_api in usable))
                self._get('device_selected_dict')[module] = usable[0][1]

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
        if sys.platform == 'win32' and 'sounddevice' not in sys.modules:
            os.environ.setdefault(SD_ENABLE_ASIO, '1')
        try:
            import sounddevice
            if sys.platform == 'win32' and '-asio' not in os.path.basename(getattr(sounddevice, '_libname', '')):
                self._show_message('ASIO is not available: SoundDevice was imported before the plug-in, '
                                   'or it uses a PortAudio library without ASIO')
            host_apis = [host_api['name'] for host_api in sounddevice.query_hostapis()]
            return [(card['index'], card['name'], host_apis[card['hostapi']])
                    for card in sounddevice.query_devices()]
        except (ImportError, OSError) as e:
            # sounddevice raises an OSError when the PortAudio library is missing
            self._show_message(f'Could not import sounddevice: {e}')
            return []

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
            self.device_index = self._find_device()

            if self.module == PYALSAAUDIO:
                self._open_alsa()
            elif self.module == SOUNDDEVICE:
                self._open_sounddevice()

            self._set('device', self.device)
            if self.module != PYALSAAUDIO:
                self._show_message(f'Host API: {self.device_host_api}')
                self._set_var('host_api', self.device_host_api)
            soundcard = self._soundcard()
            self._show_message(f'Sound card: {soundcard}')
            self._set_var('soundcard', soundcard)
            self._log_actual_sizes()
            if self.module != PYALSAAUDIO:
                self._log_portaudio_latency()
            self._set('silence_frames', self._silence_frames())
            self.experiment.cleanup_functions.append(self.close)
        elif self.dummy_mode == 'yes':
            self._set('device', None)
            self._set('silence_frames', 0)
            self._set_var('soundcard', 'dummy mode')
            self._set_var('period_size_actual', 'dummy mode')
            self._set_var('buffer_size_actual', 'dummy mode')
            if self.module != PYALSAAUDIO:
                self._set_var('host_api', 'dummy mode')
                self._set_var('portaudio_latency', 'dummy mode')
            self._show_message('Dummy mode enabled, run phase')
        else:
            raise OSException(f'Dummy mode should be yes or no, not {self.dummy_mode}')

    def _find_device(self):
        """Returns the library's index of the chosen device. SoundDevice:
        only the devices of the chosen host API count; with duplicate names
        the first device is used.
        """
        device_list = self._get('device_dict')[self.module]
        positions = range(len(device_list))
        if self.module != PYALSAAUDIO and self.host_api != ALL_HOST_APIS:
            host_api_list = self._get('host_api_dict')[self.module]
            if self.host_api in UNUSABLE_HOST_APIS:
                raise OSException(f'Host API {self.host_api} can\'t be used: {UNUSABLE_HOST_APIS[self.host_api]}\n\n'
                                  f'Available host APIs: {", ".join([ALL_HOST_APIS] + host_api_list)}')
            if self.host_api not in host_api_list:
                raise OSException(f'Host API {self.host_api} is not available for module {self.module}\n\n'
                                  f'Available host APIs: {", ".join([ALL_HOST_APIS] + host_api_list)}')
            host_apis = self._get('device_host_api_dict')[self.module]
            positions = [i for i in positions if host_apis[i] == self.host_api]
        names = [device_list[i] for i in positions]
        if self.device_name not in names:
            host_api = self._get('unusable_device_dict')[self.module].get(self.device_name)
            if host_api is not None and self.host_api in (ALL_HOST_APIS, host_api):
                raise OSException(f'Device {self.device_name} uses {host_api}, which the plugin can\'t use: '
                                  f'{UNUSABLE_HOST_APIS[host_api]}\n\n'
                                  f'Available devices: {", ".join(names)}')
            host_api_text = f' and host API {self.host_api}' if self.host_api != ALL_HOST_APIS and self.module != PYALSAAUDIO else ''
            raise OSException(f'Device {self.device_name} is not available for module {self.module}{host_api_text}\n\n'
                              f'Available devices: {", ".join(names)}')
        position = positions[names.index(self.device_name)]
        self.device_host_api = self._get('device_host_api_dict')[self.module][position]
        return self._get('device_index_dict')[self.module][position]

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
        self.buffer_size_actual = buffer_size

    def _silence_frames(self):
        """Returns the number of frames of silence that the play items write
        after a sound and at a pause, else 0. In WASAPI exclusive mode the
        sound card plays its buffer again as long as no new data comes in
        (PortAudio 19.7.0 fills it only while the items write; heard as
        ringing after a sound): the whole WASAPI buffer, as PortAudio
        reports it (buffer_size_actual), else PortAudio's latency plus one
        period, which covers it.
        """
        if self.kind != 'play' or not self.wasapi_exclusive:
            return 0
        if isinstance(self.buffer_size_actual, int) and self.buffer_size_actual > 0:
            frames = self.buffer_size_actual
        else:
            frames = math.ceil(self.device.latency * self.samplerate) + self.period_size
        self._show_message(f'WASAPI exclusive mode: {frames} frames of silence after each sound and at a pause')
        return frames

    def _log_portaudio_latency(self):
        """Logs the latency in ms that PortAudio reports for the stream."""
        # PortAudio reports the latency in seconds
        latency = self.device.latency * 1000
        self._show_message(f'PortAudio latency: {latency} ms')
        self._set_var('portaudio_latency', latency)

    def _wasapi_buffer_size(self):
        """Returns the size in frames of the WASAPI buffer of a SoundDevice
        stream, or 'unknown' for the other Windows host APIs.
        """
        import sounddevice

        hostapi = sounddevice.query_hostapis(sounddevice.query_devices(self.device_index)['hostapi'])
        if hostapi['name'] != WASAPI:
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
        """Returns the card, PCM device and subdevice number of the opened
        device, as in /proc/asound/card<card>/pcm<device><p|c>/sub<subdevice>,
        or None.
        """
        if self.module == PYALSAAUDIO:
            # Also for plug and dmix devices: ALSA reports the card below
            # them; -1 when the device is not on a sound card (e.g.
            # pipewire, null)
            device_info = self.device.info()
            if device_info['card_no'] < 0:
                return None
            return device_info['card_no'], device_info['device_no'], device_info['subdevice_no']
        hw = re.search(PORTAUDIO_HW_DEVICE, self.device_name)
        if not hw:
            return None
        # PortAudio doesn't report the subdevice
        return int(hw.group(1)), int(hw.group(2)), 0

    def _read_hw_params(self):
        """Returns buffer size, period size, channels and sample rate from
        /proc/asound/card<card>/pcm<device><p|c>/sub<subdevice>/hw_params,
        or None.
        """
        pcm = self._hw_pcm()
        if pcm is None:
            return None
        card, device_number, subdevice = pcm
        direction = 'p' if self.kind == 'play' else 'c'
        filename_alsa = os.path.join(ASOUND_PATH, f'card{card}', f'pcm{device_number}{direction}',
                                     f'sub{subdevice}', 'hw_params')
        try:
            with open(filename_alsa) as f:
                params = dict(line.split(':', 1) for line in f if ':' in line)
            # e.g. "rate: 44100 (44100/1)"
            return (int(params['buffer_size']), int(params['period_size']),
                    int(params['channels']), int(params['rate'].split()[0]))
        except (OSError, KeyError, ValueError, IndexError):
            # e.g. "closed" when another program changed the device
            return None

    def _open_sounddevice(self):
        import sounddevice

        extra_settings = None
        if self.wasapi_exclusive:
            extra_settings = sounddevice.WasapiSettings(exclusive=True)
            self._show_message('WASAPI exclusive mode')
        stream_class = sounddevice.RawOutputStream if self.kind == 'play' else sounddevice.RawInputStream
        # PortAudio makes its host buffer the period size plus the
        # suggested latency (WASAPI exclusive; ALSA and WASAPI shared: plus
        # at least one period), so this asks for a buffer of the chosen
        # number of periods; PortAudio and the sound card round it (see
        # buffer_size_actual)
        latency = (self.periods - 1) * self.period_size / self.samplerate
        try:
            self.device = stream_class(samplerate=float(self.samplerate),
                                       dtype=SOUNDDEVICE_FORMATS[self.bitdepth],
                                       blocksize=int(self.period_size),
                                       latency=latency,
                                       device=int(self.device_index),
                                       channels=int(self.channels),
                                       extra_settings=extra_settings)
            self._show_message("Audio device opened")
            self.device.start()
        except Exception as e:
            default_samplerate = sounddevice.query_devices(self.device_index)['default_samplerate']
            raise OSException(
                f'Could not start audio device\n\nMessage: {e}{self._sample_rate_hint(e, default_samplerate)}')

    def _sample_rate_hint(self, error, default_samplerate):
        """Returns an explanation for a sample rate that WASAPI refuses in
        shared mode or that an ASIO driver refuses, with the device's default
        sample rate from PortAudio (WASAPI: the rate of the Windows sound
        settings; ASIO: the driver's current rate), else ''.
        """
        if str(PA_INVALID_SAMPLE_RATE) not in str(error):
            return ''
        rate = round(default_samplerate)
        if self.device_host_api == WASAPI and not self.wasapi_exclusive:
            alternative = f'WASAPI exclusive mode (host API {WASAPI})'
            return ('\n\nIn shared mode, WASAPI only accepts the sample rate that is set for the device in the '
                    f'Windows sound settings ({rate} Hz): choose that sample rate or {alternative}')
        if self.device_host_api == ASIO:
            not_working = ': the driver may not work at all' if rate == 0 else ''
            return (f'\n\nThe ASIO driver refuses this sample rate. Its current sample rate is {rate} Hz'
                    f'{not_working}. Check the settings in the driver\'s control panel')
        return ''

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
        if self.module == PYAUDIO:
            # Also in dummy mode, so that a test fails like the lab would
            raise OSException(f'{PYAUDIO} is no longer supported: choose {SOUNDDEVICE}, '
                              f'which lists the same devices')
        self.device_name = self.var.device_name
        self.host_api = self.var.host_api
        wasapi_exclusive = self.var.wasapi_exclusive
        if wasapi_exclusive not in ('yes', 'no'):
            raise OSException(f'WASAPI exclusive mode should be yes or no, not {wasapi_exclusive}')
        # Only with SoundDevice and the host API setting WASAPI (the GUI
        # disables the setting otherwise)
        self.wasapi_exclusive = wasapi_exclusive == 'yes' and self.module == SOUNDDEVICE and self.host_api == WASAPI
        if wasapi_exclusive == 'yes' and self.module == SOUNDDEVICE and not self.wasapi_exclusive:
            self._show_message(f'WASAPI exclusive mode is not used: it needs host API {WASAPI}')

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
        self._set('buffer_size', self.buffer_size)
        self._set('periods', self.periods)
        self._set('buffer_time', round(self.periods * self.period_time, 1))

        self._set_var('module', self.module)
        self._set_var('device_name', self.device_name)
        self._set_var('period_size', self.period_size)
        self._set_var('period_time_exact', self.period_time_exact)
        self._set_var('period_time', self.period_time)
        self._set_var('buffer_size', self.buffer_size)
        self._set_var('periods', self.periods)
        self._set_var('buffer_time', self._get('buffer_time'))
        if self.module == SOUNDDEVICE:
            self._set_var('wasapi_exclusive', 'yes' if self.wasapi_exclusive else 'no')
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
            device.close()

            delattr(self.experiment, f'audio_low_latency_{self.kind}_device')
            # Not set when another init item opened the device
            if hasattr(self, 'device'):
                del self.device
            self._show_message("Audio device closed")
        except Exception as e:
            oslogger.warning(f'failed to close audio device: {e}')
