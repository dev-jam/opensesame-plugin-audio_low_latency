"""Low Latency Audio - waits until the background audio playback has finished"""

# The category determines the group for the plugin in the item toolbar
category = "Audio Low Latency Playback"
# Defines the GUI controls
controls = [
    {
        "type": "text",
        "label": "<small><b>Note:</b> Audio Low Latency Play Init item at the begin of the experiment is needed for initialization of the audio device</small>"
    }, {
        "type": "text",
        "label": "<small>Audio Low Latency version 10.3.0</small>"
    }
]