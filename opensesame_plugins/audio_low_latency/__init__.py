from importlib.metadata import PackageNotFoundError, version

# These packages will be checked by the updater extension for updates on
# conda and pip
packages = ['opensesame-plugin-audio_low_latency']

try:
    __version__ = version(packages[0])
except PackageNotFoundError:
    # Running from a source folder that is not installed
    __version__ = 'unknown'
