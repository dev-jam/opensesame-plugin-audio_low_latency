"""Low Latency Audio - waits until the background audio recording has finished"""

# The category determines the group for the plugin in the item toolbar
category = "Audio Low Latency Recording"
# Defines the GUI controls
controls = [
    {
        "type": "text",
        "label": "<small><b>Note:</b> Audio Low Latency Record Init item at the begin of the experiment is needed for initialization of the audio device</small>"
    }, {
        "type": "text",
        "label": "<small>Audio Low Latency version 10.0.2</small>"
    }
]