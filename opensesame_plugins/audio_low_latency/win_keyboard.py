"""
This file is part of OpenSesame.

OpenSesame is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

OpenSesame is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with OpenSesame.  If not, see <http://www.gnu.org/licenses/>.

Key presses for the background items under Windows.

The OpenSesame keyboard (pygame, pyglet) can't be read from a thread under
Windows, so the background items read the key state directly with
GetAsyncKeyState() of user32. This doesn't use the event queue of the
backend: a key press is also seen when the experiment window doesn't have
the focus, and it stays in the event queue for later keyboard items.
"""

__author__ = "Bob Rosbag"
__license__ = "GPLv3"

import ctypes
import time

from libopensesame.exceptions import OSException

# Seconds to sleep when no key was pressed, like the 1 ms timeout of the
# keyboard of the other platforms
POLL_TIME = 0.001
# High bit of GetAsyncKeyState(): the key is down
KEY_DOWN = 0x8000

# OpenSesame key names to Windows virtual-key codes
VIRTUAL_KEYS = {
    'space': 0x20, 'return': 0x0D, 'tab': 0x09, 'backspace': 0x08,
    'left': 0x25, 'up': 0x26, 'right': 0x27, 'down': 0x28,
    'insert': 0x2D, 'delete': 0x2E, 'home': 0x24, 'end': 0x23,
    'pageup': 0x21, 'pagedown': 0x22,
}
VIRTUAL_KEYS.update({chr(c): ord(chr(c).upper()) for c in range(ord('a'), ord('z') + 1)})
VIRTUAL_KEYS.update({str(d): 0x30 + d for d in range(10)})
VIRTUAL_KEYS.update({f'f{n}': 0x6F + n for n in range(1, 13)})


class WinKeyboard:
    """Reports a key when it goes down, for the keys of a key list."""

    def __init__(self, clock, keylist):
        unknown = [key for key in keylist if key.lower() not in VIRTUAL_KEYS]
        if unknown:
            raise OSException(
                f'Key(s) {", ".join(unknown)} not supported for the background items '
                f'under Windows\n\nSupported keys: a-z, 0-9, f1-f12, '
                f'{", ".join(k for k in VIRTUAL_KEYS if len(k) > 1 and not k[1:].isdigit())}')
        self.clock = clock
        self.keylist = list(keylist)
        self._user32 = ctypes.windll.user32
        self._down = {}

    def _is_down(self, key):
        return bool(self._user32.GetAsyncKeyState(VIRTUAL_KEYS[key.lower()]) & KEY_DOWN)

    def flush(self):
        """Keys that are down now are not reported until they go up again."""
        self._down = {key: self._is_down(key) for key in self.keylist}

    def get_key(self):
        """Returns (key, time) of the first key that went down since the
        last call, or (None, time).
        """
        pressed = None
        for key in self.keylist:
            down = self._is_down(key)
            if down and not self._down.get(key, False) and pressed is None:
                pressed = key
            self._down[key] = down
        if pressed is None:
            time.sleep(POLL_TIME)
        return pressed, self.clock.time()
