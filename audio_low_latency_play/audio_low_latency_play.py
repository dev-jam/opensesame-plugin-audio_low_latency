#-*- coding:utf-8 -*-

"""
22-10-2017
Author: Bob Rosbag
Version: 2017.11-1

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

#import warnings

from libopensesame.py3compat import *
from libopensesame import debug
from libopensesame.item import item
from libqtopensesame.items.qtautoplugin import qtautoplugin
from libopensesame.exceptions import osexception
from openexp.keyboard import keyboard
import wave


VERSION = u'2017.11-1'

class audio_low_latency_play(item):

    """
    Class handles the basic functionality of the item.
    It does not deal with GUI stuff.
    """

    # Provide an informative description for your plug-in.
    description = u'Low Latency Audio: starts audio playback on the foreground.'

    def __init__(self, name, experiment, string=None):

        item.__init__(self, name, experiment, string)
        self.verbose = u'no'
        self.poll_time = 10


    def reset(self):

        """Resets plug-in to initial values."""

        # Set default experimental variables and values
        self.var.filename = u''
        self.var.duration_check = u'no'
        self.var.duration = 0
        self.var.ram_cache = u'yes'


    def init_var(self):

        """Set en check variables."""

        if hasattr(self.experiment, "audio_low_latency_play_dummy_mode"):
            self.dummy_mode = self.experiment.audio_low_latency_play_dummy_mode
            self.verbose = self.experiment.audio_low_latency_play_verbose
            if self.dummy_mode == u'no':
                self.module = self.experiment.audio_low_latency_play_module
                self.device = self.experiment.audio_low_latency_play_device
                self.device_name = self.experiment.audio_low_latency_play_device_name
                self.device_index = self.experiment.audio_low_latency_play_device_index
                self.audio_buffer = self.experiment.audio_low_latency_play_buffer
        else:
            raise osexception(
                    u'Audio Low Latency Play Init item is missing')

        self.filename = self.experiment.pool[self.var.filename]
        self.ram_cache = self.var.ram_cache


    def prepare(self):

        """Preparation phase"""

        # Call the parent constructor.
        item.prepare(self)

        # create keyboard object
        self.kb = keyboard(self.experiment,timeout=1)

        self.init_var()

        if self.dummy_mode == u'no':
            try:
                self.show_message(u'\n')
                self.show_message(u'Loading sound file: '+self.filename+' ...')
                self.wav_file = wave.open(self.filename, 'rb')
                self.show_message(u'Succesfully loaded sound file...')
            except Exception as e:
                raise osexception(
                    u'Could not load audio file', exception=e)

            self.buffer_time = round(float(self.audio_buffer) / float(self.wav_file.getframerate()) * 1000, 1)

            self.experiment.var.audio_low_latency_play_bitdepth = self.wav_file.getsampwidth()*8
            self.experiment.var.audio_low_latency_play_samplerate = self.wav_file.getframerate()
            self.experiment.var.audio_low_latency_play_channels = self.wav_file.getnchannels()
            self.experiment.var.audio_low_latency_play_buffer_time = self.buffer_time

            self.show_message(u'Bitdepth: ' +str(self.wav_file.getsampwidth()*8)+'bit')
            self.show_message(u'Samplerate: ' + str(self.wav_file.getframerate())+ 'Hz')
            self.show_message(u'Channels: ' + str(self.wav_file.getnchannels()))
            self.show_message(u'Buffer: ' + str(self.buffer_time)+'ms')

            self.frame_size = self.wav_file.getsampwidth() * 8 * self.wav_file.getnchannels()
            self.period_size = self.audio_buffer #* frame_size
            self.data_size = self.frame_size * self.period_size

            if self.module == u'PyAlsaAudio (Low Latency)':
                import alsaaudio
                self.device.close()
                self.device = alsaaudio.PCM(type=alsaaudio.PCM_PLAYBACK, device=self.device_name)
                self.experiment.audio_low_latency_play_device = self.device
                self.device.setchannels(self.wav_file.getnchannels())
                self.device.setrate(self.wav_file.getframerate())

                # 8bit is unsigned in wav files
                if self.wav_file.getsampwidth() == 1:
                    try:
                        self.device.setformat(alsaaudio.PCM_FORMAT_U8)
                    except Exception as e:
                        raise osexception(
                            u'Device does not support ' + str(self.wav_file.getsampwidth()*8) + u'bit audio', exception=e)
                # Otherwise we assume signed data, little endian
                elif self.wav_file.getsampwidth() == 2:
                    try:
                        self.device.setformat(alsaaudio.PCM_FORMAT_S16_LE)
                    except Exception as e:
                        raise osexception(
                            u'Device does not support ' + str(self.wav_file.getsampwidth()*8) + u'bit audio', exception=e)
                elif self.wav_file.getsampwidth() == 3:
                    raise osexception(
                        u'24bit will be supported in the next release')
#                    try:
#                        self.device.setformat(alsaaudio.PCM_FORMAT_S24_3LE)
#                    except Exception as e:
#                        raise osexception(
#                            u'Device does not support ' + str(self.wav_file.getsampwidth()*8) + u'bit audio', exception=e)
                elif self.wav_file.getsampwidth() == 4:
                    try:
                        self.device.setformat(alsaaudio.PCM_FORMAT_S32_LE)
                    except Exception as e:
                        raise osexception(
                            u'Device does not support ' + str(self.wav_file.getsampwidth()*8) + u'bit audio', exception=e)
                else:
                    raise ValueError('Unsupported format')

                self.device.setrate(self.wav_file.getframerate())
                self.device.setperiodsize(self.period_size)
                self.audio_stream = self.device
                self.experiment.audio_low_latency_play_stream = self.audio_stream
            elif self.module == u'PyAudio (Compatibility)':
               if self.wav_file.getsampwidth() == 4:
                    raise osexception(
                        u'32bit not yet supported')
               else:
                    try:
                        
                        if hasattr(self.experiment, "audio_low_latency_play_stream"):
                            self.experiment.audio_low_latency_play_stream.close()

                        self.audio_stream = self.device.open(format=self.device.get_format_from_width(self.wav_file.getsampwidth()),
                                channels=self.wav_file.getnchannels(),
                                rate=self.wav_file.getframerate(),
                                output=True,
                                frames_per_buffer=self.period_size,
                                output_device_index=self.device_index)
                        self.experiment.audio_low_latency_play_stream = self.audio_stream
                    except Exception as e:
                        raise osexception(
                            u'Could not start audio device', exception=e)

            if self.ram_cache == u'yes':
                wav_file_nframes = self.wav_file.getnframes()
                self.wav_file_data = self.wav_file.readframes(wav_file_nframes)
                self.wav_file.close()


    def run(self):

        """Run phase"""

        self.duration = self.var.duration
        self.duration_check  = self.var.duration_check

        self.set_item_onset()

        if not (hasattr(self.experiment, "audio_low_latency_play_stop") or hasattr(self.experiment, "audio_low_latency_play_wait")):
            raise osexception(
                    u'Audio Low Latency Play Stop or Audio Low Latency Play Wait item is missing')

        if self.dummy_mode == u'no':
            while self.experiment.audio_low_latency_play_locked:
                self.clock.sleep(self.poll_time)
            
            self.show_message(u'Starting audio')
            if self.ram_cache == u'No':
                self.play_file(self.audio_stream, self.wav_file, self.period_size)
            elif self.ram_cache == u'yes':
                self.play_data(self.audio_stream, self.wav_file_data, self.data_size)
        elif self.dummy_mode == u'yes':
            self.show_message(u'Dummy mode enabled, NOT playing audio')
        else:
            self.show_message(u'Error with dummy mode!')


    def play_file(self, stream, wav_file, chunk):

        data = wav_file.readframes(chunk)
        self.experiment.var.audio_low_latency_play_onset = self.clock.time()
        start_time = self.clock.time()

        while len(data) > 0:
            # Read data from stdin
            stream.write(data)
            data = wav_file.readframes(chunk)

            if self.duration_check == u'yes':
                time_passed = (self.clock.time() - start_time) * 1000
                if time_passed >= self.duration:
                    break

        if self.module == u'PyAudio (Compatibility)':
            stream.stop_stream()  # stop stream
        
        #stream.close()
        wav_file.close()

        self.show_message(u'Stopped audio')


    def play_data(self, stream, wav_data, chunk):

        self.experiment.var.audio_low_latency_play_onset = self.clock.time()
        start_time = self.clock.time()

        for start in range(0,len(wav_data),chunk):
            stream.write(wav_data[start:start+chunk])

            if self.duration_check == u'yes':
                time_passed = (self.clock.time() - start_time) * 1000
                if time_passed >= self.duration:
                    break

        if self.module == u'PyAudio (Compatibility)':
            stream.stop_stream()  # stop stream
        
        #stream.close()
        self.show_message(u'Stopped audio')


    def show_message(self, message):
        """
        desc:
            Show message.
        """

        debug.msg(message)
        if self.verbose == u'yes':
            print(message)


class qtaudio_low_latency_play(audio_low_latency_play, qtautoplugin):

    def __init__(self, name, experiment, script=None):

        """plug-in GUI"""

        audio_low_latency_play.__init__(self, name, experiment, script)
        qtautoplugin.__init__(self, __file__)
        self.text_version.setText(
        u'<small>Audio Low Latency version %s</small>' % VERSION)

    def apply_edit_changes(self):

        """
        desc:
            Applies the controls.
        """

        if not qtautoplugin.apply_edit_changes(self) or self.lock:
            return False
        self.custom_interactions()

    def edit_widget(self):

        """
        Refreshes the controls.

        Returns:
        The QWidget containing the controls
        """

        if self.lock:
            return
        self.lock = True
        w = qtautoplugin.edit_widget(self)
        self.custom_interactions()
        self.lock = False
        return w

    def custom_interactions(self):

        """
        desc:
            Activates the relevant controls for each tracker.
        """
        if self.var.duration_check == u'yes':
            self.spinbox_duration.setEnabled(True)
        elif self.var.duration_check == u'no':
            self.spinbox_duration.setDisabled(True)
