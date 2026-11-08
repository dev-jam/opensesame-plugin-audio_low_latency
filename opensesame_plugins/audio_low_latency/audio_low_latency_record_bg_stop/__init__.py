# Copyright (C) 2017-2026 Bob Rosbag <mail@bobrosbag.nl> and contributors
# SPDX-License-Identifier: GPL-3.0-or-later

"""Low Latency Audio - stops the background audio recording"""

from .. import __version__

# The category determines the group for the plugin in the item toolbar
category = "Audio Low Latency Recording"
# The item type of this item in experiments made before 14.0.0
aliases = ["audio_low_latency_record_stop"]
# Defines the GUI controls
controls = [
    {
        "type": "text",
        "label": "<small><b>Note:</b> Audio Low Latency Record Init item at the beginning of the experiment is needed for initialization of the audio device</small>"
    }, {
        "type": "text",
        "label": f"<small>Audio Low Latency version {__version__}</small>"
    }
]
