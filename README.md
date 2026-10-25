OpenSesame Plug-in: Audio Low Latency
==========

*An OpenSesame plug-in for playing and recording audio files with low latency.*  

Copyright, 2022, Bob Rosbag


## About

The main goal of this plug-in is to play and record audio with minimal and predictable latencies to achieve a high accuracy and precision. The 'PyAlsaAudio' package which uses the Linux ALSA audio system provided the best results within Python. 
'PortAudio' and 'sounddevice' are cross-platform and work on both Windows and Linux.

This plug-in consists of playback and recording items as well as foreground and background (multi-threaded) items.
Both playback and recording have their own *init* item. These should be placed at the beginning of an experiment.


Difference between foreground and background:

- **Foreground** items play/record until the file ends or the set duration has passed. 
- **Background** items consist of a 'start', 'wait' and 'stop' item. These are fully multi-threaded. After the start of the playback/recording, the item will immediately advance to the next item. When it reaches the 'stop' or 'wait' item, it will stop the audio or wait until the file ends or duration has passed.


Seven items for playback:

- **Play Init** initialization of the playback audio device, this should be placed at the beginning of an experiment.

Foreground:
- **Play** starts the playback of audio, it will play the entire audio file or will stop after the set duration has passed before continuing to the next item in the experiment.

Background:
- **Play Start** starts the playback of audio, it will directly advance to the next item in the experiment.
- **Play Wait** waits until the thread from 'Play Start' is finished (end of audio or surpassing the duration) before advancing to the next item in the experiment.
- **Play Stop** sends a stop signal to the 'Play Start' thread to stop immediately and checks if the thread has finished.

- **Play Pause** pauses playback of audio.
- **Play Resume** resumes playback of audio.


Seven items for recording:

- **Record Init** initialization of the recording audio device, this should be placed at the beginning of an experiment.

Foreground:
- **Record** starts the recording of audio, it will record for the set duration before continuing to the next item in the experiment.

Background:
- **Record Start** starts the recording of audio, it will directly advance to the next item in the experiment.
- **Record Wait** waits until the thread from 'Record Start' is finished (surpassing the duration) before advancing to the next item in the experiment.
- **Record Stop** sends a stop signal to the 'Record Start' thread to stop immediately and checks if the thread has finished.

- **Record Pause** pauses recording of audio.
- **Record Resume** resumes recording of audio.


Linux (SoundDevice): devices of PortAudio's OSS host API (/dev/dsp, the OSS emulation of the kernel) are not listed: they bypass ALSA, so the sound card and the actual sizes can't be found; use PyAlsaAudio, or the ALSA devices of SoundDevice. An experiment with such a device gives an error.

PyAudio is no longer supported (after 12.0.2): an experiment with module "PyAudio (PortAudio)" gives an error; choose "SoundDevice (PortAudio)", which lists the same devices (the latency may differ).

Variables in the log file ([kind] is play or record):

- Init items: audio_low_latency_[kind]_module, _device_name, _period_size, _period_time, _period_time_exact, _periods, _buffer_size (the period size times the number of periods), _buffer_time (SoundDevice doesn't use these three, PortAudio chooses the buffer: see _buffer_size_actual), _bitdepth, _samplewidth, _samplerate and _channels; and audio_low_latency_[kind]_soundcard, _period_size_actual and _buffer_size_actual (see below); with SoundDevice also audio_low_latency_[kind]_portaudio_latency: the latency in ms that PortAudio reports for the stream, and audio_low_latency_[kind]_host_api: the host API of the device, e.g. "Windows WASAPI" (on all systems, "dummy mode" in dummy mode); with SoundDevice also audio_low_latency_[kind]_wasapi_exclusive (yes when WASAPI exclusive mode is used, else no).
- Play, record and start items: the timestamps time_stimulus_onset_[item_name] and time_stimulus_offset_[item_name] (no offset in dummy mode).
- Keys: audio_low_latency_[kind]_key_presses and audio_low_latency_[kind]_key_timestamps (play and record items), audio_low_latency_[kind]_start_key_presses and audio_low_latency_[kind]_start_key_timestamps (start items), separated by ';'.
- Play and play start items: wav_duration and wait_to_finish (in ms; wait_to_finish not in dummy mode).

The sound card (audio_low_latency_[kind]_soundcard) is found as follows:

- Linux (PyAlsaAudio, and the "(hw:X,Y)" devices of SoundDevice): the codec of an onboard (HD Audio) device, e.g. "Realtek ALC1220", else the name of the card, e.g. "MOTU M2", from /proc/asound. Devices that are not on a sound card, such as "default" with a sound server, "pipewire" or "null", give "unknown".
- Windows and macOS (SoundDevice): the device name, e.g. "Speakers (Realtek(R) Audio)".
- In dummy mode: "dummy mode".

The period size and buffer size that are actually used, in frames (audio_low_latency_[kind]_period_size_actual and _buffer_size_actual):

- Linux (PyAlsaAudio devices on a sound card, also through a plug or dmix device such as "default:CARD=X", and the "(hw:X,Y)" devices of SoundDevice): the hardware parameters of the sound card, from /proc/asound. With PyAlsaAudio, a period size or number of periods other than the chosen one is an error; with SoundDevice, a period size other than the chosen one is a warning in the debug window (they have no buffer size setting: PortAudio chooses the buffer size). Other devices, such as "default" with a sound server, "pipewire" or "null", give "unknown".
- Windows, SoundDevice with a WASAPI device: the buffer size of WASAPI (from PortAudio); the period size is "unknown". Other host APIs (MME, ASIO) give "unknown" for both: PortAudio doesn't report them.
- macOS: "unknown".
- In dummy mode: "dummy mode".

Windows (SoundDevice, through PortAudio):

- Host API: Windows lists most devices once per host API (MME, Windows WASAPI, ...), often with the same name. Choose the host API in the init item to see only its devices; with "all", a name that occurs more than once uses the first device (MME). MME and WASAPI in shared mode play and record through the Windows mixer: Windows may convert the bit depth and the sample rate, and the latency is higher (MME the highest). WASAPI in shared mode only accepts the sample rate set in the Windows sound settings. The host API choice also works on Linux and macOS.
- WASAPI exclusive mode (SoundDevice): the device is used by the experiment alone, without the Windows mixer, so the bit depth, sample rate and buffer reach the sound card; the device must support them, or it can't be opened. Other programs can't play sound on that device during the experiment. It can only be switched on with host API "Windows WASAPI"; with another host API it is not used. In exclusive mode the sound card plays its buffer again as long as no new data comes in (between sounds the items write nothing), which sounds as ringing after a sound that doesn't end in silence: the play items therefore write one buffer of silence after each sound and when they pause, so they end about one buffer (e.g. 43 ms) later, when the sound has been played.
- ASIO: the plug-in makes SoundDevice load its PortAudio library with ASIO (it sets the environment variable SD_ENABLE_ASIO before SoundDevice is imported), so ASIO devices are listed. This doesn't work when SoundDevice was imported before the plug-in (e.g. by an inline script) or uses another PortAudio library (e.g. from conda). PortAudio loads every installed ASIO driver when SoundDevice is imported, also when an ASIO device isn't used. The ASIO buffer size is set in the driver's control panel; PortAudio doesn't report the buffer it uses, so the actual sizes are "unknown".
- DirectSound and WDM-KS devices are not listed: the items play and record with blocking reads and writes, which PortAudio does not support for them (with DirectSound nothing was played or recorded, without an error; WDM-KS devices could not be opened). An experiment with such a device gives an error.



## License

This software is distributed under the terms of the GNU General Public License 3. The full license should be included in the file `COPYING`, or can be obtained from:

- <http://www.gnu.org/licenses/gpl.txt>

This plug-in contains works of others. Icons are derivatives of the Faience icon theme, Faenza icon theme and Papirus icon theme.


## Documentation

Installation instructions and documentation on OpenSesame are available on the documentation website:

- <http://osdoc.cogsci.nl/>
