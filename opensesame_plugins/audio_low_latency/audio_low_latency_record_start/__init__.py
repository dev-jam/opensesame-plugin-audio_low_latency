"""Low Latency Audio - starts audio recording in the background"""

from .. import __version__

# The category determines the group for the plugin in the item toolbar
category = "Audio Low Latency Recording"
# Defines the GUI controls
controls = [
    {
        "type": "line_edit",
        "var": "filename",
        "label": "Audio Filename (without .wav)",
        "name": "line_edit_filename"
    }, {
        "type": "checkbox",
        "var": "file_exists_action",
        "label": "Do not overwrite existing files, automatically append suffix",
        "name": "checkbox_file_exists_action"
    }, {
        "type": "line_edit",
        "var": "duration",
        "label": "Duration (ms or infinite)",
        "name": "line_edit_duration"
    }, {
        "type": "line_edit",
        "var": "delay_start",
        "label": "Start delay (ms)",
        "name": "line_edit_delay_start"
    }, {
        "type": "line_edit",
        "var": "delay_stop",
        "label": "Stop delay (ms)",
        "name": "line_edit_delay_stop"
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
        "label": "Cache to RAM",
        "name": "checkbox_ram_cache"
    }, {
        "type": "text",
        "label": "<b>IMPORTANT:</b> this is a multi-threaded background item, it will immediately advance to the next item, it will NOT wait for the recording to finish."
    }, {
        "type": "text",
        "label": "<small><b>Note:</b> Audio Low Latency Record Init item at the beginning of the experiment is needed for initialization of the audio device</small>"
    }, {
        "type": "text",
        "label": f"<small>Audio Low Latency version {__version__}</small>"
    }
]
