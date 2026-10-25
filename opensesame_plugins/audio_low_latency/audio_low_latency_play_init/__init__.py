"""Low Latency Audio - initializes the playback audio device"""

from .. import __version__

# The category determines the group for the plugin in the item toolbar
category = "Audio Low Latency Playback"
# Defines the GUI controls
controls = [
    {
        "type": "checkbox",
        "var": "dummy_mode",
        "label": "Dummy Mode",
        "name": "checkbox_dummy"
    }, {
        "type": "checkbox",
        "var": "verbose",
        "label": "Verbose Mode",
        "name": "checkbox_verbose"
    }, {
       "type": "combobox",
       "var": "module",
       "label": "Module",
       "options": [
       ],
       "name": "combobox_module"
    }, {
       "type": "combobox",
       "var": "host_api",
       "label": "Host API (SoundDevice)",
       "options": [
       ],
       "name": "combobox_host_api"
    }, {
        "type": "checkbox",
        "var": "wasapi_exclusive",
        "label": "WASAPI exclusive mode (SoundDevice)",
        "name": "checkbox_wasapi_exclusive"
    }, {
       "type": "combobox",
       "var": "device_name",
       "label": "Device",
       "options": [
       ],
       "name": "combobox_device_name"
    }, {
        "type": "line_edit",
        "var": "bitdepth",
        "label": "Bit Depth (8, 16, 24 or 32)",
        "name": "line_edit_bitdepth"
    }, {
        "type": "line_edit",
        "var": "samplerate",
        "label": "Sample Rate (Hz)",
        "name": "line_edit_samplerate"
    }, {
        "type": "line_edit",
        "var": "channels",
        "label": "Channels",
        "name": "line_edit_channels"
    }, {
        "type": "line_edit",
        "var": "period_size",
        "label": "Period size (frames)",
        "name": "line_edit_period_size"
    }, {
        "type": "line_edit",
        "var": "periods",
        "label": "Number of periods per buffer",
        "name": "line_edit_periods"
    }, {
        "type": "text",
        "label": "<small><b>Note:</b> Audio Low Latency Play Init item at the beginning of the experiment is needed for initialization of the audio device</small>"
    }, {
        "type": "text",
        "label": f"<small>Audio Low Latency version {__version__}</small>"
    }
]
