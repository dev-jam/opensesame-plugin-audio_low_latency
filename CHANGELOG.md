# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

## [Unreleased]

- fixed: since 12.0.0, the play items checked the duration between the stimulus onset and the first write of the audio device; the first write follows the onset directly again, as in 11.0.1
- fixed: a start item reported a stop or wait item as missing when that item was prepared before it, e.g. a stop item after a loop with the start item; and a pause item reported a missing resume item or key when a later start item in the same sequence was prepared after the resume item
- fixed: while an item waited for a background playback or recording of the same kind to end, it held up that playback or recording with the legacy backend, which caused underruns with small buffers (e.g. 2 periods of 128 frames); it also unlocked the device just before its thread ended, so in rare cases two later items could play or record at the same time
- fixed: an error in a background playback or recording was lost when the next start item came before a wait or stop item; that start item now raises it. An error that no wait or stop item raised (e.g. it was skipped) is a warning in the log at the end
- changed: an error in a background thread while the experiment ends (e.g. the closed keyboard after an error or a user abort) is no longer stored in `audio_low_latency_<play|record>_thread_error`
- fixed: a pause/resume or stop key could be lost, most often a resume key during a pause (then the playback or recording stayed paused and a wait item waited forever; 5 of 36 test runs with the legacy backend); the items no longer flush the keyboard after each key check. As a result, other events during the playback or recording (e.g. mouse clicks, and with the psycho backend other keys) are no longer discarded: a later response item with flush disabled sees them
- fixed: a paused playback or recording with pause/resume or stop keys used a full CPU core (12.0.0 fixed this only without keys)
- changed: clearer messages: a PyAudio device that can't be opened (e.g. an unsupported number of channels) gives "Could not open audio device" instead of "16bit audio not supported"; the duration errors say that sound/infinite or a positive integer is allowed (they said "greater than 1", but 1 is accepted) and show the value; spelling fixes

## [12.0.0] - 2026-10-18

- fixed: an error in a background playback or recording (e.g. an unplugged device) is raised by the wait or stop item; before, it was only printed, the experiment continued and a later item of the same kind waited forever
- fixed: a stop, wait, pause or resume item without a running start item (e.g. a skipped start item, or a stop item after a wait item) waited forever; now it is an error
- fixed: a background playback or recording that still runs at the end of the experiment (after an error or a user abort) is stopped before the audio device is closed
- fixed: a start item after a pause item without a resume item started paused
- fixed: the stop signal of a stop item right after a start item could be lost
- changed: the stop, wait, pause and resume items no longer check every 100 ms whether the thread of the start item has started
- fixed: a paused background playback or recording without pause/resume keys used a full CPU core
- fixed: after a stop key, the play item waited for the rest of the duration of the sound before going on
- fixed: 24 bit audio with PyAlsaAudio always failed (since 11.0.0) and played or recorded wrong data before: it now uses the packed format S24_3LE, as in a wave file
- fixed: PyAudio recording used the default input device instead of the selected device
- fixed: the init items check the hardware parameters of the selected ALSA device (`DEV=n`); before, they always read those of device 0
- fixed: init items without PortAudio devices or without the PortAudio library could not be loaded; a module without devices is no longer listed
- fixed: clear errors for a module or device that is not available (e.g. an experiment made on another computer), a device that can't be opened, an invalid dummy mode, and a bit depth other than 8, 16, 24 or 32; sample rate, channels, period size and periods must be positive
- fixed: failing to close the audio device is a warning in the log
- fixed: the description of the record pause item said that it waits until the recording has finished
- fixed: spaces around keys in the pause/resume and stop lists (`a; b`) made those keys never match; a list without keys (`;`) is now an error instead of a crash
- fixed: an invalid preload/cache setting played or recorded nothing without an error
- fixed: an empty recording filename saved the recording next to the log folder (`data_1.wav`); now an error
- fixed: a stop, wait, pause or resume item without any start item gave "An unexpected error occurred"
- fixed: PyAudio recording failed with "Input overflowed" when the stream had not been read for a while (e.g. between trials)
- fixed: SoundDevice recording failed when a period was not a multiple of 8 bytes (e.g. 8 bit mono)
- fixed: with the psycho backend, the key list of the pause/resume and stop keys grew with every key check
- removed: the numpy dependency (no longer used)
- added: a warning in the log after ALSA buffer underruns (periods of the sound not played) and overruns (parts of the recording missing); before, they were silent
- changed: the code shared by the items is in base modules next to the item folders; the items without their own GUI no longer have a GUI class (OpenSesame creates the same one) and don't import Qt
- changed: the record init item also logs `audio_low_latency_record_period_time` and `audio_low_latency_record_period_time_exact`, as the play init item does
- changed: the play start item logs `wait_to_finish` as 0 after a stop, as the play item does
- changed: the record pause and resume items set `audio_low_latency_record_execute_pause` to 1 and 0 (was True and False), and the record stop and wait items set `audio_low_latency_record_stop`/`_wait` to True (was 1), as the play items do
- changed: all "item is missing" messages name the item in backticks
- removed: the ossaudiodev code (it was not enabled, and Python 3.13 no longer has ossaudiodev) and `experiment.oss4_module_name`
- changed: the version in the items is read from the installed package (`unknown` when running from a source folder that is not installed)
- added: pause/resume and stop keys of the background items work under Windows: they read the key state with `GetAsyncKeyState()`, because the OpenSesame keyboard can't be read in a thread there (11.0.0 disabled these keys). Keys: a-z, 0-9, f1-f12 and a few named keys; a press is also seen when the experiment window doesn't have the focus
- changed: with a fixed duration, playback including pauses no longer exceeds the duration: a period that would end after the duration is not played (the playback ends at most one period early); a pause that lasts until the duration stops the playback without resuming it (before, about one buffer of sound played after the pause); audio queued before a late resume is cut at the duration; and the play item no longer waits afterwards for the pause time (before, it ended at duration + pause). A sound shorter than the duration still waits until the duration, pauses included. A duration shorter than one period is an error
- changed: with *Do not overwrite existing files*, a suffix is only added when the file exists, and it is added to the name as entered: `subject_1` becomes `subject_1_1.wav` when `subject_1.wav` exists. Before, a recording `rec` was always saved as `rec_1.wav`, and `subject_1` as `subject_2.wav`, the name of the next subject

## [11.0.1] - 2026-10-12

- added bg sleep method for sleep outside the main thread
- set continue variable to 1 at every start

## [11.0.0] - 2026-10-09

- bg items are now fixed under Windows. Stop, pause and resume keys are disabled under Windows when set and give a warning
- remove wait correction, interferes with the stop key
- added bit depth check

## [10.9.1] - 2025-09-28

- more precise placement of lock
- bg item: always join the thread

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

[Unreleased]: https://github.com/dev-jam/opensesame-plugin-audio_low_latency/compare/12.0.0...HEAD
[12.0.0]: https://github.com/dev-jam/opensesame-plugin-audio_low_latency/compare/11.0.1...12.0.0
[11.0.1]: https://github.com/dev-jam/opensesame-plugin-audio_low_latency/compare/11.0.0...11.0.1
[11.0.0]: https://github.com/dev-jam/opensesame-plugin-audio_low_latency/compare/10.9.1...11.0.0
[10.9.1]: https://github.com/dev-jam/opensesame-plugin-audio_low_latency/compare/10.9.0...10.9.1
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
