OpenSesame Plug-in: Audio Low Latency
==========

*An OpenSesame Plug-in for playing and recording audio files with low latency on Linux.*  

Copyright, 2020, Bob Rosbag  


1. About
--------

The main goal of this plug-in is to play and record audio files with as low and stable latencies as possible. The 'PyAlsaAudio' package which uses the Linux ALSA audio system provided the best results within Python. 
For compatibility reasons the 'PortAudio' option was added so experiments can be created and fully executed on Windows systems. 'PortAudio' is cross-platform and works on both Windows as Linux but gives higher and more variable latencies than the 'alsaaudio' option.
To fully utilize this plug-in you need a Linux system with ALSA and the 'alsasound' package (version 0.8.4 or higher). The 'PyAlsaAudio' package (named python-alsasound) in the Debian and Ubuntu repositories is outdated, therefore I added packages for the Debian testing/unstable and stretch distribution.
Python2 packages are for the normal version of OpenSesame and the Python3 packages are for the future/experimental version of OpenSesame. These packages are built for Debian and not tested in Ubuntu. The Python package is also available on pypi and the source on github:

https://github.com/larsimmisch/pyalsaaudio


This *init* item should be placed at the beginning of an experiment.

Audio Low Latency Record Init options:

- *Dummy Mode* for testing experiments.
- *Verbose Mode* for testing experiments.
- *Module* selection of audio module.
- *Device* selection of audio device.
- *Bit depth* number of bits per sample.
- *Sample Rate* number of samples/second.
- *Channels* number of channels.
- *Period size* is a positive integer and represents the number of frames.



2. LICENSE
----------

The Audio Low Latency Plug-in is distributed under the terms of the GNU General Public License 3.
The full license should be included in the file COPYING, or can be obtained from

- <http://www.gnu.org/licenses/gpl.txt>

This plug-in contains works of others. For the full license information, please
refer to `debian/copyright`.


3. Documentation
----------------

Installation instructions and documentation on OpenSesame are available on the documentation website:

- <http://osdoc.cogsci.nl/>
