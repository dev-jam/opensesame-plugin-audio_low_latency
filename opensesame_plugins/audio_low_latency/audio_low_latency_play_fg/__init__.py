# Copyright (C) 2017-2026 Bob Rosbag <mail@bobrosbag.nl> and contributors
# SPDX-License-Identifier: GPL-3.0-or-later

"""Low Latency Audio - starts audio playback in the foreground"""

from .. import __version__

# The category determines the group for the plugin in the item toolbar
category = "Audio Low Latency Playback"
# The item type of this item in experiments made before 14.0.0
aliases = ["audio_low_latency_play"]
# Defines the GUI controls
controls = [
    {
        "type": "filepool",
        "var": "filename",
        "label": "Audio Filename",
        "name": "filepool_filename"
    }, {
        "type": "line_edit",
        "var": "duration",
        "label": "Duration (ms or sound)",
        "name": "line_edit_duration"
    }, {
        "type": "line_edit",
        "var": "delay",
        "label": "Delay (ms)",
        "name": "line_edit_delay"
    }, {
        "type": "line_edit",
        "var": "pause_resume",
        "label": "Pause/Resume keys (separated by ;)",
        "name": "line_edit_pause_resume"
    }, {
        "type": "line_edit",
        "var": "stop",
        "label": "Stop keys (separated by ;)",
        "name": "line_edit_stop"
    }, {
        "type": "checkbox",
        "var": "ram_cache",
        "label": "Preload",
        "name": "checkbox_ram_cache"
    }, {
        "type": "text",
        "label": "<b>IMPORTANT:</b> this is a foreground item, it will wait for the playback to finish before advancing to the next item."
    }, {
        "type": "text",
        "label": "<small><b>Note:</b> Audio Low Latency Play Init item at the beginning of the experiment is needed for initialization of the audio device</small>"
    }, {
        "type": "text",
        "label": f"<small>Audio Low Latency version {__version__}</small>"
    }
]
