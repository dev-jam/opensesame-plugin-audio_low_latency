#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Author: Bob Rosbag
2022

This plug-in is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This software is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this plug-in.  If not, see <http://www.gnu.org/licenses/>.
"""
import os
from setuptools import setup


def get_readme():

    if os.path.exists('README.md'):
        with open('README.md') as fd:
            return fd.read()
    return 'No readme information'


setup(
    name='opensesame-plugin-audio_low_latency',
    version='9.1.0',
    description='An OpenSesame Plug-in for playing and recording audio files with low latency on Linux.',
    long_description=get_readme(),
    long_description_content_type='text/markdown',
    author='Bob Rosbag',
    author_email='debian@bobrosbag.nl',
    url='https://github.com/dev-jam/opensesame-plugin-audio_low_latency',
    # Classifiers used by PyPi if you upload the plugin there
    classifiers=[
        'Intended Audience :: Science/Research',
        'Topic :: Scientific/Engineering',
        'Environment :: MacOS X',
        'Environment :: Win32 (MS Windows)',
        'Environment :: X11 Applications',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Programming Language :: Python :: 3',
    ],
    packages=[],
    data_files=[
        ('share/opensesame_plugins/audio_low_latency_play',
        # Then a list of files that are copied into the target folder. Make sure
        # that these files are also included by MANIFEST.in!
        [
            'opensesame_plugins/audio_low_latency_play/audio_low_latency_play.md',
            'opensesame_plugins/audio_low_latency_play/audio_low_latency_play.png',
            'opensesame_plugins/audio_low_latency_play/audio_low_latency_play_large.png',
            'opensesame_plugins/audio_low_latency_play/audio_low_latency_play.py',
            'opensesame_plugins/audio_low_latency_play/info.yaml',
            ]
        ),
        ('share/opensesame_plugins/audio_low_latency_play_init',
        [
            'opensesame_plugins/audio_low_latency_play_init/audio_low_latency_play_init.md',
            'opensesame_plugins/audio_low_latency_play_init/audio_low_latency_play_init.png',
            'opensesame_plugins/audio_low_latency_play_init/audio_low_latency_play_init_large.png',
            'opensesame_plugins/audio_low_latency_play_init/audio_low_latency_play_init.py',
            'opensesame_plugins/audio_low_latency_play_init/info.yaml',
            ]
        ),
        ('share/opensesame_plugins/audio_low_latency_play_start',
        [
            'opensesame_plugins/audio_low_latency_play_start/audio_low_latency_play_start.md',
            'opensesame_plugins/audio_low_latency_play_start/audio_low_latency_play_start.png',
            'opensesame_plugins/audio_low_latency_play_start/audio_low_latency_play_start_large.png',
            'opensesame_plugins/audio_low_latency_play_start/audio_low_latency_play_start.py',
            'opensesame_plugins/audio_low_latency_play_start/info.yaml',
            ]
        ),
        ('share/opensesame_plugins/audio_low_latency_play_stop',
        [
            'opensesame_plugins/audio_low_latency_play_stop/audio_low_latency_play_stop.md',
            'opensesame_plugins/audio_low_latency_play_stop/audio_low_latency_play_stop.png',
            'opensesame_plugins/audio_low_latency_play_stop/audio_low_latency_play_stop_large.png',
            'opensesame_plugins/audio_low_latency_play_stop/audio_low_latency_play_stop.py',
            'opensesame_plugins/audio_low_latency_play_stop/info.yaml',
            ]
        ),
        ('share/opensesame_plugins/audio_low_latency_play_wait',
        [
            'opensesame_plugins/audio_low_latency_play_wait/audio_low_latency_play_wait.md',
            'opensesame_plugins/audio_low_latency_play_wait/audio_low_latency_play_wait.png',
            'opensesame_plugins/audio_low_latency_play_wait/audio_low_latency_play_wait_large.png',
            'opensesame_plugins/audio_low_latency_play_wait/audio_low_latency_play_wait.py',
            'opensesame_plugins/audio_low_latency_play_wait/info.yaml',
            ]
        ),
        ('share/opensesame_plugins/audio_low_latency_play_pause',
        [
            'opensesame_plugins/audio_low_latency_play_pause/audio_low_latency_play_pause.md',
            'opensesame_plugins/audio_low_latency_play_pause/audio_low_latency_play_pause.png',
            'opensesame_plugins/audio_low_latency_play_pause/audio_low_latency_play_pause_large.png',
            'opensesame_plugins/audio_low_latency_play_pause/audio_low_latency_play_pause.py',
            'opensesame_plugins/audio_low_latency_play_pause/info.yaml',
            ]
        ),
        ('share/opensesame_plugins/audio_low_latency_play_resume',
        [
            'opensesame_plugins/audio_low_latency_play_resume/audio_low_latency_play_resume.md',
            'opensesame_plugins/audio_low_latency_play_resume/audio_low_latency_play_resume.png',
            'opensesame_plugins/audio_low_latency_play_resume/audio_low_latency_play_resume_large.png',
            'opensesame_plugins/audio_low_latency_play_resume/audio_low_latency_play_resume.py',
            'opensesame_plugins/audio_low_latency_play_resume/info.yaml',
            ]
        ),
        ('share/opensesame_plugins/audio_low_latency_record',
        [
            'opensesame_plugins/audio_low_latency_record/audio_low_latency_record.md',
            'opensesame_plugins/audio_low_latency_record/audio_low_latency_record.png',
            'opensesame_plugins/audio_low_latency_record/audio_low_latency_record_large.png',
            'opensesame_plugins/audio_low_latency_record/audio_low_latency_record.py',
            'opensesame_plugins/audio_low_latency_record/info.yaml',
            ]
        ),
        ('share/opensesame_plugins/audio_low_latency_record_init',
        [
            'opensesame_plugins/audio_low_latency_record_init/audio_low_latency_record_init.md',
            'opensesame_plugins/audio_low_latency_record_init/audio_low_latency_record_init.png',
            'opensesame_plugins/audio_low_latency_record_init/audio_low_latency_record_init_large.png',
            'opensesame_plugins/audio_low_latency_record_init/audio_low_latency_record_init.py',
            'opensesame_plugins/audio_low_latency_record_init/info.yaml',
            ]
        ),
        ('share/opensesame_plugins/audio_low_latency_record_start',
        [
            'opensesame_plugins/audio_low_latency_record_start/audio_low_latency_record_start.md',
            'opensesame_plugins/audio_low_latency_record_start/audio_low_latency_record_start.png',
            'opensesame_plugins/audio_low_latency_record_start/audio_low_latency_record_start_large.png',
            'opensesame_plugins/audio_low_latency_record_start/audio_low_latency_record_start.py',
            'opensesame_plugins/audio_low_latency_record_start/info.yaml',
            ]
        ),
        ('share/opensesame_plugins/audio_low_latency_record_stop',
        [
            'opensesame_plugins/audio_low_latency_record_stop/audio_low_latency_record_stop.md',
            'opensesame_plugins/audio_low_latency_record_stop/audio_low_latency_record_stop.png',
            'opensesame_plugins/audio_low_latency_record_stop/audio_low_latency_record_stop_large.png',
            'opensesame_plugins/audio_low_latency_record_stop/audio_low_latency_record_stop.py',
            'opensesame_plugins/audio_low_latency_record_stop/info.yaml',
            ]
        ),
        ('share/opensesame_plugins/audio_low_latency_record_wait',
        [
            'opensesame_plugins/audio_low_latency_record_wait/audio_low_latency_record_wait.md',
            'opensesame_plugins/audio_low_latency_record_wait/audio_low_latency_record_wait.png',
            'opensesame_plugins/audio_low_latency_record_wait/audio_low_latency_record_wait_large.png',
            'opensesame_plugins/audio_low_latency_record_wait/audio_low_latency_record_wait.py',
            'opensesame_plugins/audio_low_latency_record_wait/info.yaml',
            ]
        ),
        ('share/opensesame_plugins/audio_low_latency_record_pause',
        [
            'opensesame_plugins/audio_low_latency_record_pause/audio_low_latency_record_pause.md',
            'opensesame_plugins/audio_low_latency_record_pause/audio_low_latency_record_pause.png',
            'opensesame_plugins/audio_low_latency_record_pause/audio_low_latency_record_pause_large.png',
            'opensesame_plugins/audio_low_latency_record_pause/audio_low_latency_record_pause.py',
            'opensesame_plugins/audio_low_latency_record_pause/info.yaml',
            ]
        ),
        ('share/opensesame_plugins/audio_low_latency_record_resume',
        [
            'opensesame_plugins/audio_low_latency_record_resume/audio_low_latency_record_resume.md',
            'opensesame_plugins/audio_low_latency_record_resume/audio_low_latency_record_resume.png',
            'opensesame_plugins/audio_low_latency_record_resume/audio_low_latency_record_resume_large.png',
            'opensesame_plugins/audio_low_latency_record_resume/audio_low_latency_record_resume.py',
            'opensesame_plugins/audio_low_latency_record_resume/info.yaml',
            ]
        )]
    )
