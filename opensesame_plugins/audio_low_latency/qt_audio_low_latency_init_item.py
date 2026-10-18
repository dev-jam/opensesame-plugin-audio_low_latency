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
"""

__author__ = "Bob Rosbag"
__license__ = "GPLv3"

from libqtopensesame.items.qtautoplugin import QtAutoPlugin

from .audio_low_latency_item import PYALSAAUDIO


class QtAudioLowLatencyInitItem(QtAutoPlugin):
    """GUI of the init items: the device list follows the chosen module, the
    module and device are disabled in dummy mode, and the number of periods
    is only enabled for PyAlsaAudio.
    """

    def init_edit_widget(self):
        super().init_edit_widget()
        module_list = self._get('module_list')
        device_dict = self._get('device_dict')
        if not module_list:
            return

        if self.var.module in module_list:
            self.current_module = self.var.module
        else:
            self.current_module = module_list[0]
            self.var.module = self.current_module

        if self.var.device_name in device_dict[self.current_module]:
            self.current_device_name = self.var.device_name
        else:
            self.current_device_name = device_dict[self.current_module][0]
            self._get('device_selected_dict')[self.current_module] = self.current_device_name
            self.var.device_name = self.current_device_name

        device_index = device_dict[self.current_module].index(self.current_device_name)

        self.combobox_module.clear()
        self.combobox_module.addItems(module_list)
        self.combobox_module.setCurrentIndex(module_list.index(self.current_module))

        self.combobox_device_name.clear()
        self.combobox_device_name.addItems(device_dict[self.current_module])
        self.combobox_device_name.setCurrentIndex(device_index)

    def apply_edit_changes(self):
        if not QtAutoPlugin.apply_edit_changes(self) or self.lock:
            return False
        self.custom_interactions()
        return True

    def edit_widget(self):
        if self.lock:
            return
        self.lock = True
        w = QtAutoPlugin.edit_widget(self)
        self.custom_interactions()
        self.lock = False
        return w

    def custom_interactions(self):
        if not hasattr(self, 'current_module'):
            # No modules with devices
            return
        if self.current_module != self.var.module:
            device_dict = self._get('device_dict')
            device_selected_dict = self._get('device_selected_dict')
            device_selected_dict[self.current_module] = self.var.device_name

            new_module_name = self.var.module
            new_device_name = device_selected_dict[new_module_name]
            new_device_index = device_dict[new_module_name].index(new_device_name)

            self.combobox_device_name.clear()
            self.combobox_device_name.addItems(device_dict[new_module_name])
            self.combobox_device_name.setCurrentIndex(new_device_index)

            self.current_module = new_module_name
            self.current_device_name = new_device_name
            self.var.device_name = self.current_device_name

        if self.var.dummy_mode == 'yes':
            self.combobox_module.setDisabled(True)
            self.combobox_device_name.setDisabled(True)
        elif self.var.dummy_mode == 'no':
            self.combobox_module.setEnabled(True)
            self.combobox_device_name.setEnabled(True)

        self.line_edit_periods.setEnabled(self.current_module == PYALSAAUDIO)
