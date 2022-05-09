OpenSesame Plug-in: Audio Low Latency
==========

*An OpenSesame Plug-in for playing and recording audio files with low latency on Linux.*  

Copyright, 2022, Bob Rosbag  


1. About
--------

The main goal of this plug-in is to play and record audio with minimal and predictable latencies to achieve a high accuracy and precision. The 'PyAlsaAudio' package which uses the Linux ALSA audio system provided the best results within Python. 
For compatibility reasons the 'PortAudio' and 'sounddevice' options were added so experiments can be created and fully executed on Windows systems. 'PortAudio' and 'sounddevice' are cross-platform and work on both Windows as Linux but these give a higher and more variable latency than the 'alsaaudio' option.
To fully utilize this plug-in you need a Linux system with ALSA and the 'PyAlsaAudio' package (version 0.8.4 or higher). In Debian and Ubuntu this package is named python3-pyalsaaudio. The Python package is also available on pypi and the source on github:

https://github.com/larsimmisch/pyalsaaudio


The plug-in has an *init* item which should be placed at the beginning of an experiment.


2. LICENSE
----------

The Audio Low Latency Plug-in is distributed under the terms of the GNU General Public License 3.
The full license should be included in the file COPYING, or can be obtained from

- <http://www.gnu.org/licenses/gpl.txt>

This plug-in contains works of others.


3. Documentation
----------------

Installation instructions and documentation on OpenSesame are available on the documentation website:

- <http://osdoc.cogsci.nl/>
