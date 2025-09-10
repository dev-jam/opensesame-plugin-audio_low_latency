# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

## [Unreleased]


## [10.9.0] - 2025-09-10

- fixed early break off of audio playback in pyalsaaudio
- replaced the incorrect pcm.drop() with pcm.drain() for pyalsaaudio
- added padding to fill incomplete periods with silence (other backends)
- removed last excessive write attempt of empty data

## [10.8.0] - 2025-09-05

- convert string handling to f-strings

## [10.7.0] - 2025-07-17

- license cleanup
- improved resetting and closing audio device

## [10.6.2] - 2024-05-31

- also record items: correct accidental removal of item onset
    
## [10.6.1] - 2024-05-30

- correct accidental removal of item onset
    
## [10.6.0] - 2024-04-16

- duration check during pause in recording items
    
## [10.5.0] - 2024-04-14

- additional fix for offset correction for the stop function
- added logging of stop and pause/resume keypresses and timestamps
    
## [10.4.0] - 2024-04-13

- fixed offset correction for the stop function
- fixed reporting of duration of the recording
    
## [10.3.0] - 2023-12-04

- fixed item dependency checks when running an experiment
- small bug fixes
    
## [10.2.0] - 2023-11-12

- preload bugfixes
- playback bugfixes
- added buffer control
- increased and improved verbosity
- debug tools added
    
## [10.0.2] - 2023-08-30

- fixed dependencies
- save recordings in log file folder
    
## [10.0.0] - 2023-08-15

- new style api OpenSesame 4.0
- lots of small fixes and code cleanup
    
## [9.3.0] - 2023-08-13

Final release for OpenSesame 3 API

- small bugfixes
    
## [v9.2.0] - 2023-04-18

- bug fixes
    
## [8.9.0] - 2022-11-25

- new plugin code style
- debian packaging fixed
    
## [8.7.0] - 2022-10-21

- implemented undocumented info method for checking parameters
    
## [8.6.0] - 2022-10-14

Changes:

- Removed deprecated methods from pyalsaaudio and use linux cli to check parameters
- Small corrections
    
## [8.5.0] - 2022-07-07

New features:

-  audio recordings are saved in the experiment folder by default (thanks to Flavier Sebastien)
-  option added to prevent overwriting recordings, suffix is added when needed (thanks to Flavier Sebastien)
-  wav extension is added automatically (thanks to Flavier Sebastien)
-  audio recording is not cached by default (to prevent losing the entire recording when crashing)
    
## [8.4.0] - 2022-06-06

Bugfixes:

- corrected period size for play item when using cache
- merged play_file and play_data into play
    
## [8.3.0] - 2022-06-04

Bugfixes:

- fix for numpy data conversion for sounddevice by Flavier Sebastien
    
## [8.2.0] - 2022-06-02

Bugfixes:

- Fixed PyAudio
- Fixed Sounddevice
    
## [v8.0.2] - 2022-05-24

Bug fixes:

- fixed new parameters not Initializing
- increased verbosity

## v8.0.0 - 2022-05-20

- moved several checks to prepare phase
- fixed wav duration bug
- implemented delay for stopping the audio recording 

[Unreleased]: https://github.com/dev-jam/opensesame-plugin-audio_low_latency/compare/10.9.0...HEAD
[10.9.0]: https://github.com/dev-jam/opensesame-plugin-audio_low_latency/compare/10.8.0...10.9.0
[10.8.0]: https://github.com/dev-jam/opensesame-plugin-audio_low_latency/compare/10.7.0...10.8.0
[10.7.0]: https://github.com/dev-jam/opensesame-plugin-audio_low_latency/compare/10.6.2...10.7.0
[10.6.2]: https://github.com/dev-jam/opensesame-plugin-audio_low_latency/compare/10.6.1...10.6.2
[10.6.1]: https://github.com/dev-jam/opensesame-plugin-audio_low_latency/compare/10.6.0...10.6.1
[10.6.0]: https://github.com/dev-jam/opensesame-plugin-audio_low_latency/compare/10.5.0...10.6.0
[10.5.0]: https://github.com/dev-jam/opensesame-plugin-audio_low_latency/compare/10.4.0...10.5.0
[10.4.0]: https://github.com/dev-jam/opensesame-plugin-audio_low_latency/compare/10.3.0...10.4.0
[10.3.0]: https://github.com/dev-jam/opensesame-plugin-audio_low_latency/compare/10.2.0...10.3.0
[10.2.0]: https://github.com/dev-jam/opensesame-plugin-audio_low_latency/compare/10.0.2...10.2.0
[10.0.2]: https://github.com/dev-jam/opensesame-plugin-audio_low_latency/compare/10.0.0...10.0.2
[10.0.0]: https://github.com/dev-jam/opensesame-plugin-audio_low_latency/compare/9.3.0...10.0.0
[9.3.0]: https://github.com/dev-jam/opensesame-plugin-audio_low_latency/compare/v9.2.0...9.3.0
[v9.2.0]: https://github.com/dev-jam/opensesame-plugin-audio_low_latency/compare/8.9.0...v9.2.0
[8.9.0]: https://github.com/dev-jam/opensesame-plugin-audio_low_latency/compare/8.7.0...8.9.0
[8.7.0]: https://github.com/dev-jam/opensesame-plugin-audio_low_latency/compare/8.6.0...8.7.0
[8.6.0]: https://github.com/dev-jam/opensesame-plugin-audio_low_latency/compare/8.5.0...8.6.0
[8.5.0]: https://github.com/dev-jam/opensesame-plugin-audio_low_latency/compare/8.4.0...8.5.0
[8.4.0]: https://github.com/dev-jam/opensesame-plugin-audio_low_latency/compare/8.3.0...8.4.0
[8.3.0]: https://github.com/dev-jam/opensesame-plugin-audio_low_latency/compare/8.2.0...8.3.0
[8.2.0]: https://github.com/dev-jam/opensesame-plugin-audio_low_latency/compare/v8.0.2...8.2.0
[v8.0.2]: https://github.com/dev-jam/opensesame-plugin-audio_low_latency/compare/v8.0.0...v8.0.2
