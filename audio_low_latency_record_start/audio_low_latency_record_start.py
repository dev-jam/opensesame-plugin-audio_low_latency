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
import threading
import time
import wave
#from libopensesame.file_pool_store import file_pool_store


VERSION = u'2017.11-1'

class audio_low_latency_record_start(item):

    """
    Class handles the basic functionality of the item.
    It does not deal with GUI stuff.
    """

    # Provide an informative description for your plug-in.
    description = u'Low Latency Audio: starts audio recording in the background.'

    def __init__(self, name, experiment, string=None):

        item.__init__(self, name, experiment, string)
        self.verbose = u'no'
        self.poll_time = 0.01


    def reset(self):

        """Resets plug-in to initial values."""

        # Set default experimental variables and values
        self.var.filename = u''
        self.var.duration_check = u'no'
        self.var.duration = 0
        self.var.bitdepth = str(16)
        self.var.samplerate = str(44100)
        self.var.channels = str(2)
        self.var.ram_cache = u'yes'

    def init_var(self):

        """Set en check variables."""

        if hasattr(self.experiment, "audio_low_latency_record_dummy_mode"):
            self.dummy_mode = self.experiment.audio_low_latency_record_dummy_mode
            self.verbose = self.experiment.audio_low_latency_record_verbose
            if self.dummy_mode == u'no':
                self.module = self.experiment.audio_low_latency_record_module
                self.device = self.experiment.audio_low_latency_record_device
                self.device_index = self.experiment.audio_low_latency_record_device_index
                self.audio_buffer = self.experiment.audio_low_latency_record_buffer

        else:
            raise osexception(
                    u'Audio Low Latency Record Init item is missing')


#        if self.var.filename in self.experiment.pool():
#            self.filename = self.experiment.pool([self.var.filename])
#            print('pool')
#        else:
#            self.filename = self.var.filename
#            print('pad')


        self.filename = self.var.filename
        self.bitdepth = int(self.var.bitdepth)
        self.samplewidth = self.bitdepth / 8
        self.samplerate = int(self.var.samplerate)
        self.channels = int(self.var.channels)
        self.ram_cache = self.var.ram_cache
        self.audio_buffer_time = round(float(self.audio_buffer) / float(self.var.samplerate) * 1000, 1)

        self.experiment.var.audio_low_latency_record_bitdepth = self.var.bitdepth
        self.experiment.var.audio_low_latency_record_samplerate = self.var.samplerate
        self.experiment.var.audio_low_latency_record_channels = self.var.channels
        self.experiment.var.audio_low_latency_record_buffer_time = self.audio_buffer_time

        self.experiment.audio_low_latency_record_continue = 1
        self.experiment.audio_low_latency_record_start = 1


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
                self.show_message(u'Creating wave file: '+self.filename+' ...')
                self.wav_file = wave.open(self.filename, 'wb')
                self.show_message(u'Succesfully created wave file...')
            except Exception as e:
                raise osexception(
                    u'Could not create wave file', exception=e)

            self.show_message(u'Bitdepth: ' +str(self.bitdepth)+'bit')
            self.show_message(u'Samplerate: ' + str(self.samplerate)+ 'Hz')
            self.show_message(u'Channels: ' + str(self.channels))
            self.show_message(u'Buffer: ' + str(self.audio_buffer_time)+'ms')

            frame_size = self.samplerate * 8 * self.channels
            self.period_size = self.audio_buffer #* frame_size

            self.wav_file.setsampwidth(self.samplewidth)
            self.wav_file.setframerate(self.samplerate)
            self.wav_file.setnchannels(self.channels)


            if self.module == u'PyAlsaAudio (Low Latency)':
                import alsaaudio

                # 8bit is unsigned in wav files
                if self.bitdepth == 8:
                    try:
                        self.device.setformat(alsaaudio.PCM_FORMAT_U8)
                    except Exception as e:
                        raise osexception(
                            u'Device does not support ' + str(self.bitdepth) + u'bit audio', exception=e)
                # Otherwise we assume signed data, little endian
                elif self.bitdepth == 16:
                    try:
                        self.device.setformat(alsaaudio.PCM_FORMAT_S16_LE)
                    except Exception as e:
                        raise osexception(
                            u'Device does not support ' + str(self.bitdepth) + u'bit audio', exception=e)
                elif self.bitdepth == 24:
                    raise osexception(
                        u'24bit will be supported in the next release')
#                    try:
#                        self.device.setformat(alsaaudio.PCM_FORMAT_S24_3LE)
#                    except Exception as e:
#                        raise osexception(
#                            u'Device does not support ' + str(self.bitdepth) + u'bit audio', exception=e)
                elif self.bitdepth == 32:
                    try:
                        self.device.setformat(alsaaudio.PCM_FORMAT_S32_LE)
                    except Exception as e:
                        raise osexception(
                            u'Device does not support ' + str(self.bitdepth) + u'bit audio', exception=e)
                else:
                    raise ValueError('Unsupported format')

                self.device.setrate(self.samplerate)
                self.device.setchannels(self.channels)
                self.device.setperiodsize(self.period_size)
                self.audio_stream = self.device
            elif self.module == u'PyAudio (Compatibility)':
               if self.bitdepth == 33:
                    raise osexception(
                        u'32bit not yet supported')
               else:
                    try:
                        self.audio_stream = self.device.open(format=self.device.get_format_from_width(self.samplewidth),
                                channels=self.channels,
                                rate=self.samplerate,
                                input=True,
                                frames_per_buffer=self.period_size,
                                output_device_index=self.device_index)
                    except Exception as e:
                        raise osexception(
                            u'Could not start audio device', exception=e)


    def run(self):

        """Run phase"""

        self.duration = self.var.duration
        self.duration_check  = self.var.duration_check

        self.set_item_onset()

        if not (hasattr(self.experiment, "audio_low_latency_record_stop") or hasattr(self.experiment, "audio_low_latency_record_wait")):
            raise osexception(
                    u'Audio Low Latency Record Stop or Audio Low Latency Record Wait item is missing')

        if self.dummy_mode == u'no':
            while self.experiment.audio_low_latency_record_locked:
                time.sleep(self.poll_time)

#            from threading import Event
#            self.experiment.ready = Event()

            self.show_message(u'Starting recording audio')
            self.experiment.audio_low_latency_record_locked = 1
            self.experiment.audio_low_latency_record_thread = threading.Thread(target=self.record, args=(self.audio_stream, self.wav_file, self.period_size))
            self.experiment.audio_low_latency_record_thread.start()
        elif self.dummy_mode == u'yes':
            self.show_message(u'Dummy mode enabled, NOT recording audio')
        else:
            self.show_message(u'Error with dummy mode!')


    def record(self, stream, wav_file, chunk):

        self.experiment.audio_low_latency_record_thread_running = 1
        frames = []
        self.experiment.var.audio_low_latency_record_start = self.clock.time()
        start_time = time.time()

        while self.experiment.audio_low_latency_record_continue:

            # Read data from device
            if self.module == u'PyAlsaAudio (Low Latency)':
                l, data = stream.read()
            elif  self.module == u'PyAudio (Compatibility)':
                data = stream.read(chunk)

            # save data to file/ram
            if self.ram_cache == u'yes':
                frames.append(data)
            elif self.ram_cache == u'no':
                wav_file.writeframes(data)

            # check for stop
            if self.duration_check == u'yes':
                time_passed = (time.time() - start_time) * 1000
                if time_passed >= self.duration:
                    break

        if self.ram_cache == u'yes':
            wav_file.writeframes(b''.join(frames))

        if self.module == u'PyAudio (Compatibility)':
            stream.stop_stream()  # stop stream
            stream.close()
        wav_file.close()

        self.show_message(u'Stopped recording audio')
        self.experiment.audio_low_latency_record_locked = 0


    def show_message(self, message):
        """
        desc:
            Show message.
        """

        debug.msg(message)
        if self.verbose == u'yes':
            print(message)


class qtaudio_low_latency_record_start(audio_low_latency_record_start, qtautoplugin):

    def __init__(self, name, experiment, script=None):

        """plug-in GUI"""

        audio_low_latency_record_start.__init__(self, name, experiment, script)
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
