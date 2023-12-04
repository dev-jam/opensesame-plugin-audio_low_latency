"""Low Latency Audio - starts audio recording on the foreground"""

# The category determines the group for the plugin in the item toolbar
category = "Audio Low Latency Recording"
# Defines the GUI controls
controls = [
    {
        "type": "line_edit",
        "var": "filename",
        "label": "Audio Filename",
        "name": "line_edit_filename",
        "tooltip": "Give output filename without extension"
    }, {
        "type": "checkbox",
        "var": "file_exists_action",
        "label": "Do not overwrite existing files, automatically append suffix",
        "name": "checkbox_file_exists_action",
        "tooltip": "If file exists append suffix to filename?"
    }, {
        "type": "line_edit",
        "var": "duration",
        "label": "Duration (ms)",
        "name": "line_edit_duration",
        "tooltip": "Value in ms"
    }, {
        "type": "line_edit",
        "var": "delay_start",
        "label": "Start delay (ms)",
        "name": "line_edit_delay_start",
        "tooltip": "Value in ms"
    }, {
        "type": "line_edit",
        "var": "delay_stop",
        "label": "Stop delay (ms)",
        "name": "line_edit_delay_stop",
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
        "label": "Cache to RAM",
        "name": "checkbox_ram_cache",
        "tooltip": "Cache to RAM before saving?"
    }, {
        "type": "text",
        "label": "<b>IMPORTANT:</b> this is a foreground item, it will wait for the recording to finish before advancing to the next item."
    }, {
        "type": "text",
        "label": "<small><b>Note:</b> Audio Low Latency Record Init item at the begin of the experiment is needed for initialization of the audio device</small>"
    }, {
        "type": "text",
        "label": "<small>Audio Low Latency version 10.3.0</small>"
    }
]
