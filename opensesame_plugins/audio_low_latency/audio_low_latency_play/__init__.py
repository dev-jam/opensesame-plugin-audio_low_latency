"""Low Latency Audio - starts audio playback on the foreground"""

# The category determines the group for the plugin in the item toolbar
category = "Audio Low Latency Playback"
# Defines the GUI controls
controls = [
    {
        "type": "filepool",
        "var": "filename",
        "label": "Audio Filename",
        "name": "filepool_filename",
        "tooltip": "Give filename"
    }, {
        "type": "line_edit",
        "var": "duration",
        "label": "Duration (ms)",
        "name": "line_edit_duration",
        "tooltip": "Value in ms"
    }, {
        "type": "line_edit",
        "var": "delay",
        "label": "Delay (ms)",
        "name": "line_edit_delay",
        "tooltip": "Value in ms"
    }, {
        "type": "line_edit",
        "var": "pause_resume",
        "label": "Pause/Resume",
        "name": "line_edit_pause_resume",
        "tooltip": "Expecting a semicolon-separated list of button characters, e.g., a;b;c"
    }, {
        "type": "line_edit",
        "var": "stop",
        "label": "Stop",
        "name": "line_edit_stop",
        "tooltip": "Expecting a semicolon-separated list of button characters, e.g., a;b;c"
    }, {
        "type": "checkbox",
        "var": "ram_cache",
        "label": "Preload",
        "name": "checkbox_ram_cache",
        "tooltip": "Preload file to RAM?"
    }, {
        "type": "text",
        "label": "<b>IMPORTANT:</b> this is a foreground item, it will wait for the playback to finish before advancing to the next item."
    }, {
        "type": "text",
        "label": "<small><b>Note:</b> Audio Low Latency Play Init item at the begin of the experiment is needed for initialization of the audio device</small>"
    }, {
        "type": "text",
        "label": "<small>Audio Low Latency version 10.3.0</small>"
    }
]
