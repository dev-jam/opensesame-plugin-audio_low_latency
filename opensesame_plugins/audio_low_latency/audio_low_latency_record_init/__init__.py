"""Low Latency Audio - initializes the recording audio device"""

# The category determines the group for the plugin in the item toolbar
category = "Audio Low Latency Recording"
# Defines the GUI controls
controls = [
    {
        "type": "checkbox",
        "var": "dummy_mode",
        "label": "Dummy Mode",
        "name": "checkbox_dummy",
        "tooltip": "Run in dummy mode"
    }, {
        "type": "checkbox",
        "var": "verbose",
        "label": "Verbose Mode",
        "name": "checkbox_verbose",
        "tooltip": "Run in verbose mode"
    }, {
       "type": "combobox",
       "var": "module",
       "label": "Choose module",
       "options": [
       ],
       "name": "combobox_module",
       "tooltip": "Module name"
    }, {
       "type": "combobox",
       "var": "device_name",
       "label": "Choose device",
       "options": [
       ],
       "name": "combobox_device_name",
       "tooltip": "hw: -> exclusive mode; plughw -> shared mode"
    }, {
        "type": "line_edit",
        "var": "bitdepth",
        "label": "Bit Depth",
        "name": "line_edit_bitdepth",
        "tooltip": "Choose bitdepth"
    }, {
        "type": "line_edit",
        "var": "samplerate",
        "label": "Sample Rate (Hz)",
        "name": "line_edit_samplerate",
        "tooltip": "Choose sample Rate"
    }, {
        "type": "line_edit",
        "var": "channels",
        "label": "Channels",
        "name": "line_edit_channels",
        "tooltip": "Channels"
    }, {
        "type": "line_edit",
        "var": "period_size",
        "label": "Period size (frames)",
        "name": "line_edit_period_size",
        "tooltip": "Period size, value is number of samples (64 seems to be the bare minimum, 65536 the maximum)"
    }, {
        "type": "line_edit",
        "var": "periods",
        "label": "Number of periods per buffer",
        "name": "line_edit_periods",
        "tooltip": "value is an integer"
    }, {
        "type": "text",
        "label": " <small><b>Note:</b> Audio Low Latency Record Init item at the begin of the experiment is needed for initialization of the audio device</small>"
    }, {
        "type": "text",
        "label": "<small>Audio Low Latency version 10.3.0</small>"
    }
]
