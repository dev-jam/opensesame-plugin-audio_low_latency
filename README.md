OpenSesame Plug-in: Audio Low Latency
==========

*An OpenSesame Plug-in for playing and recording audio files with low latency on Linux.*  

Copyright, 2022, Bob Rosbag


## 1. About
--------

The main goal of this plug-in is to play and record audio with minimal and predictable latencies to achieve a high accuracy and precision. The 'PyAlsaAudio' package which uses the Linux ALSA audio system provided the best results within Python. 
For compatibility reasons the 'PortAudio' and 'sounddevice' options were added so experiments can be created and fully executed on Windows systems. 'PortAudio' and 'sounddevice' are cross-platform and work on both Windows as Linux but these give a higher and more variable latency than the 'alsaaudio' option.
To fully utilize this plug-in you need a Linux system with ALSA and the 'PyAlsaAudio' package (version 0.8.4 or higher). In Debian and Ubuntu this package is named python3-pyalsaaudio. The Python package is also available on pypi and the source on github:

https://github.com/larsimmisch/pyalsaaudio


This plug-in consist of playback and recording items as well as foreground as background (multi-threaded) items.
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

- **Record Init** initialization of the playback audio device, this should be placed at the beginning of an experiment.

Foreground:
- **Record** starts the recording of audio, it will record for the set duration before continuing to the next item in the experiment.

Background:
- **Record Start** starts the recording of audio, it will directly advance to the next item in the experiment.
- **Record Wait** waits until the thread from 'Record Start' is finished (surpassing the duration) before advancing to the next item in the experiment.
- **Record Stop** sends a stop signal to the 'Record Start' thread to stop immediately and checks if the thread has finished.

- **Record Pause** pauses recording of audio.
- **Record Resume** resumes recording of audio.


Timestamps can be found in the log file by the name: time_stimulus_onset_[item_name]


Known bugs:

- Recording with the PyAudio module does not seem to work at the moment



## 2. LICENSE
----------

The Audio Low Latency Plug-in is distributed under the terms of the GNU General Public License 3.
The full license should be included in the file COPYING, or can be obtained from

- <http://www.gnu.org/licenses/gpl.txt>

This plug-in contains works of others. Icons are derivatives of the Faience icon theme, Faenza icon theme and Papirus icon theme.


## 3. Documentation
----------------

Installation instructions and documentation on OpenSesame are available on the documentation website:

- <http://osdoc.cogsci.nl/>
